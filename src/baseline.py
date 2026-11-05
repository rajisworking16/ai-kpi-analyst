"""LLM-only baseline: the question plus the monthly KPI totals table, no tools."""

from __future__ import annotations

from src import prompts
from src.context import AnalysisContext, kpi_table_markdown
from src.llm import LLMStats, chat_json
from src.schemas import Report


def run_baseline(ctx: AnalysisContext, stats: LLMStats | None = None) -> dict:
    """Ask the model for a report given only the monthly KPI totals."""
    messages = [
        {"role": "system", "content": prompts.BASELINE_SYSTEM},
        {"role": "user", "content": prompts.baseline_prompt(
            ctx.question, ctx.month, kpi_table_markdown(ctx))},
    ]
    return chat_json(messages, Report, stats=stats)
