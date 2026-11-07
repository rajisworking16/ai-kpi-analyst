"""Deterministic analysis context: detection, decomposition and evidence tables.

Every table the LLM sees gets an evidence id (e.g. `detection`, `decomp_revenue_category`)
so findings can cite it and the verifier can check numbers against it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd

from src.decompose import decompose, top_excess_driver
from src.detect import KPIChange, detect_from_table, shift_month
from src.kpis import DIMENSIONS, KPI_DEFINITIONS, monthly_kpis

QUESTION_KPI_PATTERNS: list[tuple[str, str]] = [
    (r"\baov\b|average order value|order value|basket", "aov"),
    (r"revenue|sales|\bgmv\b", "revenue"),
    (r"freight|shipping cost", "freight_ratio"),
    (r"late|on[- ]time", "late_rate"),
    (r"delivery (time|days)|slow deliver", "avg_delivery_days"),
    (r"review|rating|satisfaction", "avg_review_score"),
    (r"cancel", "cancellation_rate"),
    (r"payment", "orders"),
    (r"\borders\b|order count|order volume", "orders"),
]
PROMPT_TOP_ROWS = 5


@dataclass
class EvidenceTable:
    evidence_id: str
    title: str
    rows: list[dict]


@dataclass
class AnalysisContext:
    db_path: str
    month: str
    question: str
    focus_kpis: list[str]
    detection: list[KPIChange]
    decomposition: dict
    kpi_table: pd.DataFrame
    evidence: dict[str, EvidenceTable] = field(default_factory=dict)


def kpis_for_question(question: str) -> list[str]:
    """Map a question to the KPIs it asks about (deterministic keyword match)."""
    q = question.lower()
    found: list[str] = []
    for pattern, kpi in QUESTION_KPI_PATTERNS:
        if re.search(pattern, q) and kpi not in found:
            if kpi == "orders" and "aov" in found and "payment" not in q:
                continue
            found.append(kpi)
    return found


def _rows(df: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in r.items()} for r in df.to_dict("records")]


def _clean(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if hasattr(v, "item"):
        v = v.item()
    return v


def build_context(db_path: Path | str, month: str, question: str) -> AnalysisContext:
    """Run detection and decomposition for `month` and register evidence tables."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        table = monthly_kpis(con)
        detection = detect_from_table(table, month)
        focus = kpis_for_question(question)
        if not focus:
            sig = sorted((c for c in detection if c.significant),
                         key=lambda c: -abs(c.z_score or 0))
            focus = [c.kpi for c in sig[:2]] or ["revenue"]
        decomp = decompose(con, month, focus)
    finally:
        con.close()
    ctx = AnalysisContext(str(db_path), month, question, focus, detection, decomp, table)
    _register(ctx)
    return ctx


def _register(ctx: AnalysisContext) -> None:
    det_rows = [{"kpi": c.kpi, "current": c.current, "previous": c.previous,
                 "pct_change": c.pct_change, "z_score": c.z_score,
                 "trailing_mean": c.trailing_mean, "significant": c.significant}
                for c in ctx.detection]
    ctx.evidence["detection"] = EvidenceTable(
        "detection", f"KPI change detection for {ctx.month} vs {shift_month(ctx.month, -1)}",
        det_rows)
    split = {k: _clean(v) for k, v in ctx.decomposition["revenue_split"].items()}
    ctx.evidence["revenue_split"] = EvidenceTable(
        "revenue_split", "Revenue change split into volume, AOV and interaction effects", [split])
    for kpi, dims in ctx.decomposition["segments"].items():
        for dim, df in dims.items():
            eid = f"decomp_{kpi}_{dim}"
            ctx.evidence[eid] = EvidenceTable(
                eid, f"Top segments of {dim} by contribution to the change in {kpi}", _rows(df))
    ctx.evidence["kpi_table"] = EvidenceTable(
        "kpi_table", "Monthly KPI totals", _rows(ctx.kpi_table[["period", *KPI_DEFINITIONS]]))


def fmt(v) -> str:
    """Compact number formatting for prompts."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if abs(v) >= 100:
            return f"{v:.2f}"
        return f"{v:.4f}".rstrip("0").rstrip(".") if v != 0 else "0"
    return str(v)


def table_markdown(rows: list[dict], columns: list[str] | None = None,
                   max_rows: int | None = None) -> str:
    """Render rows as a Markdown table."""
    if not rows:
        return "(no rows)"
    cols = columns or list(rows[0])
    shown = rows[:max_rows] if max_rows else rows
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(fmt(r.get(c)) for c in cols) + " |" for r in shown]
    if max_rows and len(rows) > max_rows:
        lines.append(f"({len(rows) - max_rows} more rows not shown)")
    return "\n".join(lines)


DECOMP_COLUMNS_ADDITIVE = ["segment", "value_prev", "value_curr", "change", "share_of_change",
                           "volume_share", "excess_share"]
DECOMP_COLUMNS_RATE = ["segment", "value_prev", "value_curr", "change", "weight_prev",
                       "rate_effect", "mix_effect", "share_of_change", "excess_share"]


def facts_text(ctx: AnalysisContext) -> str:
    """Plain-language direction and size of each focus KPI change (deterministic)."""
    prev = shift_month(ctx.month, -1)
    by_kpi = {c.kpi: c for c in ctx.detection}
    lines = []
    for kpi in ctx.focus_kpis:
        c = by_kpi[kpi]
        pct = "n/a" if c.pct_change is None else f"{c.pct_change:+.2%}"
        flag = "significant" if c.significant else "not significant"
        lines.append(f"- {kpi} went {c.direction.upper()} from {fmt(c.previous)} in {prev} to "
                     f"{fmt(c.current)} in {ctx.month} ({pct}, {flag}).")
        drivers = []
        for dim, df in ctx.decomposition["segments"][kpi].items():
            top = top_excess_driver(df)
            if top is not None:
                drivers.append((abs(float(top["excess_contribution"])), dim, top))
        drivers.sort(key=lambda d: -d[0])
        for _size, dim, top in drivers:
            lines.append(f"  - {dim}: most disproportionate segment {top['segment']} "
                         f"(contribution {fmt(float(top['contribution']))}, volume_share "
                         f"{fmt(float(top['volume_share']))}, excess_share "
                         f"{fmt(float(top['excess_share']))})")
    s = ctx.decomposition["revenue_split"]
    if "revenue" in ctx.focus_kpis or "aov" in ctx.focus_kpis or "orders" in ctx.focus_kpis:
        lines.append(f"- Revenue change {fmt(s['total_change'])} = volume effect "
                     f"{fmt(s['volume_effect'])} + AOV effect {fmt(s['aov_effect'])} + "
                     f"interaction {fmt(s['interaction'])}.")
    return "\n".join(lines)


def context_markdown(ctx: AnalysisContext) -> str:
    """Detection + decomposition tables formatted for the agent prompt."""
    prev = shift_month(ctx.month, -1)
    parts = [f"## [detection] KPI changes, {ctx.month} vs {prev}",
             table_markdown(ctx.evidence["detection"].rows),
             "## [revenue_split] Revenue change split",
             table_markdown(ctx.evidence["revenue_split"].rows)]
    for kpi in ctx.focus_kpis:
        additive = KPI_DEFINITIONS[kpi]["kind"] == "additive"
        cols = DECOMP_COLUMNS_ADDITIVE if additive else DECOMP_COLUMNS_RATE
        for dim in DIMENSIONS:
            eid = f"decomp_{kpi}_{dim}"
            parts.append(f"## [{eid}] {ctx.evidence[eid].title} (top {PROMPT_TOP_ROWS})")
            parts.append(table_markdown(ctx.evidence[eid].rows, cols, PROMPT_TOP_ROWS))
    return "\n\n".join(parts)


def kpi_table_markdown(ctx: AnalysisContext) -> str:
    """Monthly KPI totals only (for the LLM-only baseline)."""
    return "## [kpi_table] Monthly KPI totals\n" + table_markdown(ctx.evidence["kpi_table"].rows)
