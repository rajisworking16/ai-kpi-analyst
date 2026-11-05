"""Hypothesis-testing agent loop: propose hypotheses, test them with read-only SQL, report."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from config import MAX_AGENT_STEPS, MAX_SQL_ERRORS_PER_HYPOTHESIS
from src import prompts
from src.context import AnalysisContext, context_markdown, facts_text, table_markdown
from src.detect import shift_month
from src.llm import LLMStats, chat_json
from src.schemas import AgentStep, HypothesisList, Report
from src.sql_guard import RunTrace, run_readonly

MAX_RESULT_ROWS_IN_PROMPT = 20


@dataclass
class AgentResult:
    hypotheses: list[dict]
    steps: list[dict]
    report: dict
    trace: RunTrace
    messages: list[dict]
    n_steps: int
    forced_final: bool = False
    notes: list[str] = field(default_factory=list)


def _normalize_hypotheses(raw: list[dict]) -> list[dict]:
    out, seen = [], set()
    for i, h in enumerate(raw[:5], start=1):
        hid = h.get("id") or f"H{i}"
        if hid in seen:
            hid = f"H{i}"
        seen.add(hid)
        out.append({**h, "id": hid, "status": "open", "evidence_query_ids": []})
    return out


def _status_lines(hyps: list[dict]) -> str:
    return "\n".join(f"- {h['id']} [{h['status']}]: {h['statement']}" for h in hyps)


def _all_resolved(hyps: list[dict]) -> bool:
    return all(h["status"] != "open" for h in hyps)


class _Loop:
    """State for one agent run."""

    def __init__(self, ctx: AnalysisContext, stats: LLMStats, max_steps: int):
        self.ctx, self.stats, self.max_steps = ctx, stats, max_steps
        self.trace = RunTrace()
        self.steps: list[dict] = []
        self.errors: dict[str, int] = {}
        self.messages = [
            {"role": "system", "content": prompts.AGENT_SYSTEM},
            {"role": "user", "content": prompts.hypotheses_prompt(
                ctx.question, ctx.month, shift_month(ctx.month, -1), facts_text(ctx),
                context_markdown(ctx))},
        ]
        self.hyps: list[dict] = []
        self.used = 0

    def propose(self) -> None:
        out = chat_json(self.messages, HypothesisList, stats=self.stats)
        self.used += 1
        self.hyps = _normalize_hypotheses(out["hypotheses"])
        self.messages.append({"role": "assistant", "content": json.dumps(out)})
        self.steps.append({"step": self.used, "action": "propose_hypotheses",
                           "hypotheses": self.hyps})

    def _query_ids(self) -> str:
        return ", ".join(f"{q.query_id} ({q.hypothesis_id})"
                         for q in self.trace.queries.values() if not q.error)

    def _hyp(self, hid: str) -> dict | None:
        return next((h for h in self.hyps if h["id"] == hid), None)

    def _run_sql(self, step: dict) -> str:
        hid, sql = step["hypothesis_id"], step["sql"].strip()
        if not sql:
            res_err, qid = "empty sql", "q_none"
            result = None
        else:
            result = run_readonly(sql, db_path=self.ctx.db_path, trace=self.trace,
                                  hypothesis_id=hid)
            res_err, qid = result.error, result.query_id
        step["query_id"], step["error"] = qid, res_err
        if res_err:
            self.errors[hid] = self.errors.get(hid, 0) + 1
            if self.errors[hid] >= MAX_SQL_ERRORS_PER_HYPOTHESIS and self._hyp(hid):
                self._hyp(hid)["status"] = "inconclusive"
                return (f"Query {qid} failed: {res_err}\n{hid} had "
                        f"{MAX_SQL_ERRORS_PER_HYPOTHESIS} consecutive SQL errors and is now "
                        "marked inconclusive. Move on.")
            return prompts.sql_result_message(qid, sql, "", res_err)
        self.errors[hid] = 0
        step["row_count"] = result.row_count
        md = table_markdown(result.rows, result.columns, MAX_RESULT_ROWS_IN_PROMPT)
        return prompts.sql_result_message(qid, sql, md, None)

    def _update(self, step: dict) -> str:
        h = self._hyp(step["hypothesis_id"])
        if h is None:
            return f"Unknown hypothesis id {step['hypothesis_id']}."
        status = step["status"] if step["status"] != "none" else "inconclusive"
        h["status"] = status
        h["evidence_query_ids"] = step["evidence_query_ids"]
        return f"Recorded {h['id']} as {status}."

    def iterate(self) -> bool:
        """Run steps until done. Returns True if the step limit forced the final report."""
        feedback = ""
        while self.used < self.max_steps - 1:
            content = (feedback + "\n\n" if feedback else "") + prompts.step_prompt(
                _status_lines(self.hyps), self.max_steps - self.used, self._query_ids())
            self.messages.append({"role": "user", "content": content})
            step = chat_json(self.messages, AgentStep, stats=self.stats)
            self.used += 1
            self.messages.append({"role": "assistant", "content": json.dumps(step)})
            record = {"step": self.used, **step}
            if step["action"] == "final_report":
                self.steps.append(record)
                return False
            if step["action"] == "run_sql":
                feedback = self._run_sql(record)
            else:
                feedback = self._update(record)
            self.steps.append(record)
            if _all_resolved(self.hyps):
                return False
        return True

    def final_report(self) -> dict:
        self.messages.append({"role": "user", "content": prompts.FINAL_REPORT_PROMPT})
        report = chat_json(self.messages, Report, stats=self.stats)
        self.used += 1
        self.messages.append({"role": "assistant", "content": json.dumps(report)})
        self.steps.append({"step": self.used, "action": "final_report"})
        return report


def run_agent(ctx: AnalysisContext, stats: LLMStats | None = None,
              max_steps: int = MAX_AGENT_STEPS) -> AgentResult:
    """Run the full hypothesis-testing loop and return the report plus its trace."""
    stats = stats or LLMStats()
    loop = _Loop(ctx, stats, max_steps)
    loop.propose()
    forced = loop.iterate()
    report = loop.final_report()
    return AgentResult(loop.hyps, loop.steps, report, loop.trace, loop.messages,
                       loop.used, forced)
