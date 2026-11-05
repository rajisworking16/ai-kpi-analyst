"""Pydantic schemas for every structured LLM output.

Length limits are part of the JSON schema sent to Ollama, so the constrained decoder cannot
loop forever inside a list or string (seen with greedy decoding on long evidence lists).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Id = Field(max_length=12)
ShortText = Field(max_length=300)
Name = Field(max_length=60)


class Hypothesis(BaseModel):
    id: str = Field(max_length=6, description="H1, H2, ...")
    statement: str = ShortText
    dimension: str = Field(max_length=30, description="category, customer_state, seller_id, "
                                                      "payment_type or overall")
    segment: str = Field(max_length=60, description="segment value, or 'all' for overall")
    test: str = Field(max_length=300, description="how a SQL query would test it")


class HypothesisList(BaseModel):
    hypotheses: list[Hypothesis] = Field(min_length=3, max_length=5)


class AgentStep(BaseModel):
    """One agent action. Fields not used by the chosen action are left empty."""

    action: Literal["run_sql", "update_hypothesis", "final_report"]
    hypothesis_id: str = Field(max_length=6)
    reason: str = Field(max_length=400)
    sql: str = Field(max_length=1500,
                     description="read-only SELECT/WITH query; empty unless action=run_sql")
    status: Literal["supported", "rejected", "inconclusive", "none"] = Field(
        description="hypothesis status; 'none' unless action=update_hypothesis")
    evidence_query_ids: list[str] = Field(max_length=5)


class NumberCited(BaseModel):
    value: float
    meaning: str = Field(max_length=150)


class Finding(BaseModel):
    claim: str = Field(max_length=400)
    kpi: str = Field(max_length=40)
    dimension: str = Field(max_length=30)
    segment: str = Field(max_length=60)
    numbers: list[NumberCited] = Field(max_length=6)
    evidence_query_ids: list[str] = Field(max_length=5)
    confidence: Literal["high", "medium", "low"]


class NextStep(BaseModel):
    item: str = Field(max_length=200)
    why: str = Field(max_length=250)
    data_needed: str = Field(max_length=200)


class Report(BaseModel):
    summary: str = Field(max_length=800)
    findings: list[Finding] = Field(min_length=1, max_length=4)
    investigate_next: list[NextStep] = Field(min_length=1, max_length=4)
