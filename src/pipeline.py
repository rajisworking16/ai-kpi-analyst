"""End-to-end run: context -> (baseline | agent) -> verify -> optional revision."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from config import DB_PATH, KPI_MODEL, TRACES_DIR
from src import prompts
from src.agent import run_agent
from src.baseline import run_baseline
from src.context import AnalysisContext, build_context, table_markdown
from src.llm import LLMStats, chat_json
from src.schemas import Report
from src.verify import unsupported_items, verify_report

MODES = ("baseline", "agent", "agent_verify")
AGENT_EVIDENCE_EXCLUDE = {"kpi_table"}


def _agent_sources(ctx: AnalysisContext, trace) -> tuple[dict, list[str]]:
    sources = {eid: t.rows for eid, t in ctx.evidence.items()
               if eid not in AGENT_EVIDENCE_EXCLUDE}
    always = list(sources)
    sources.update({qid: q.rows for qid, q in trace.queries.items() if not q.error})
    return sources, always


def _revise(messages: list[dict], report: dict, ver, sources: dict, stats: LLMStats) -> dict:
    items = unsupported_items(report, ver)
    unsupported_md = table_markdown(items, ["finding", "number", "where", "claim"])
    cited = list(dict.fromkeys(e for it in items for e in it["cited"]))
    evidence_md = "\n\n".join(f"[{e}]\n{table_markdown(sources[e], max_rows=15)}"
                              for e in cited) or "(no evidence cited)"
    msgs = [*messages, {"role": "user",
                        "content": prompts.revision_prompt(unsupported_md, evidence_md)}]
    return chat_json(msgs, Report, stats=stats)


def run(db_path: Path | str = DB_PATH, month: str = "2018-03",
        question: str = "Why did revenue change?", mode: str = "agent_verify",
        run_id: str | None = None, save_trace: bool = True) -> dict:
    """Run one analysis and return a JSON-serialisable run dict."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    start = time.perf_counter()
    stats = LLMStats()
    ctx = build_context(db_path, month, question)
    run_id = run_id or f"{mode}_{month}_{Path(db_path).stem}_{datetime.now():%Y%m%d%H%M%S}"
    out: dict = {"run_id": run_id, "mode": mode, "db_path": str(db_path), "month": month,
                 "question": question, "model": KPI_MODEL,
                 "prompt_version": prompts.PROMPT_VERSION, "focus_kpis": ctx.focus_kpis,
                 "detection": [c.to_dict() for c in ctx.detection],
                 "revenue_split": ctx.decomposition["revenue_split"],
                 "hypotheses": [], "steps": [], "queries": [], "revised": False,
                 "verification_before_revision": None}
    if mode == "baseline":
        report = run_baseline(ctx, stats)
        sources, always = {"kpi_table": ctx.evidence["kpi_table"].rows}, ["kpi_table"]
        n_steps, messages = 1, []
    else:
        res = run_agent(ctx, stats)
        report, n_steps, messages = res.report, res.n_steps, res.messages
        sources, always = _agent_sources(ctx, res.trace)
        out.update(hypotheses=res.hypotheses, steps=res.steps, forced_final=res.forced_final,
                   queries=[q.to_dict() for q in res.trace.queries.values()])
    ver = verify_report(report, sources, always)
    if mode == "agent_verify" and ver.unsupported_numbers > 0:
        out["verification_before_revision"] = ver.to_dict()
        out["report_before_revision"] = report
        report = _revise(messages, report, ver, sources, stats)
        ver = verify_report(report, sources, always)
        out["revised"] = True
        n_steps += 1
    out.update(report=report, verification=ver.to_dict(), n_steps=n_steps,
               llm_calls=stats.calls, llm_retries=stats.retries,
               llm_seconds=round(stats.seconds, 2), prompt_tokens=stats.prompt_tokens,
               output_tokens=stats.output_tokens,
               elapsed_s=round(time.perf_counter() - start, 2))
    if save_trace:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        (TRACES_DIR / f"{run_id}.json").write_text(json.dumps(out, indent=1, default=str))
    return out
