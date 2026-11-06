"""Render a run's final report to Markdown."""

from __future__ import annotations

from pathlib import Path

from config import REPORTS_DIR
from src.context import table_markdown

BADGES = {"verified": "🟢 verified", "partially_verified": "🟡 partially verified",
          "unsupported": "🔴 unsupported"}


def _fmt_number(n: dict) -> str:
    v = n["value"]
    return f"{v:,.4g}" if abs(v) < 1 else f"{v:,.2f}"


def render_markdown(run: dict) -> str:
    """Markdown for one run dict (as produced by src.pipeline.run)."""
    report, ver = run["report"], run["verification"]
    labels = {f["index"]: f["label"] for f in ver["findings"]}
    lines = [f"# KPI analysis: {run['question']}", "",
             f"- Month: {run['month']}  ",
             f"- Mode: {run['mode']}  ",
             f"- Model: {run['model']} (prompt {run['prompt_version']})  ",
             f"- Database: `{Path(run['db_path']).name}`  ",
             f"- Steps: {run['n_steps']}, wall time: {run['elapsed_s']:.1f}s  ",
             f"- Unsupported claim rate: {_rate(ver['unsupported_rate'])} "
             f"({ver['unsupported_numbers']}/{ver['total_numbers']} numbers)", "",
             "## Summary", "", report["summary"], "", "## Findings", ""]
    for i, f in enumerate(report["findings"]):
        lines += [f"### {i + 1}. {f['claim']}", "",
                  f"{BADGES.get(labels.get(i, ''), '')} · KPI `{f['kpi']}` · "
                  f"{f['dimension']} = `{f['segment']}` · confidence {f['confidence']}", ""]
        for n in f["numbers"]:
            lines.append(f"- {_fmt_number(n)}: {n['meaning']}")
        if f["evidence_query_ids"]:
            lines.append(f"- Evidence: {', '.join(f'`{e}`' for e in f['evidence_query_ids'])}")
        lines.append("")
    lines += ["## Investigate next", ""]
    for item in report["investigate_next"]:
        lines.append(f"- **{item['item']}**: {item['why']} (data needed: {item['data_needed']})")
    if run.get("hypotheses"):
        lines += ["", "## Hypotheses tested", "",
                  table_markdown([{"id": h["id"], "status": h["status"],
                                   "statement": h["statement"]} for h in run["hypotheses"]])]
    if run.get("queries"):
        lines += ["", "## Evidence queries", ""]
        for q in run["queries"]:
            lines += [f"**`{q['query_id']}`** ({q.get('hypothesis_id') or ''}, "
                      f"{q['row_count']} rows{', error: ' + q['error'] if q['error'] else ''})",
                      "", "```sql", q["sql"].strip(), "```", ""]
            if q["rows"]:
                lines += [table_markdown(q["rows"], q["columns"], 10), ""]
    return "\n".join(lines) + "\n"


def _rate(r: float | None) -> str:
    return "n/a" if r is None else f"{r:.1%}"


def save_report(run: dict, out_dir: Path = REPORTS_DIR) -> Path:
    """Write the Markdown report to results/reports/<run_id>.md."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run['run_id']}.md"
    path.write_text(render_markdown(run))
    return path
