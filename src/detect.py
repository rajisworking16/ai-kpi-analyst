"""Deterministic KPI change detection for a target month."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import duckdb
import pandas as pd

from config import PCT_THRESHOLD, TRAILING_MONTHS, Z_THRESHOLD
from src.kpis import KPI_NAMES, monthly_kpis


@dataclass
class KPIChange:
    """Change in one KPI for the target month."""

    kpi: str
    current: float
    previous: float
    pct_change: float | None
    z_score: float | None
    trailing_mean: float
    trailing_std: float
    direction: str
    significant: bool

    def to_dict(self) -> dict:
        return asdict(self)


def shift_month(month: str, n: int) -> str:
    """Return the month `n` months after `month` (YYYY-MM)."""
    y, m = map(int, month.split("-"))
    idx = y * 12 + (m - 1) + n
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def _clean(x: float) -> float | None:
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else float(x)


def detect_from_table(table: pd.DataFrame, month: str) -> list[KPIChange]:
    """Detect KPI changes for `month` given a monthly KPI table (one row per period)."""
    table = table.set_index("period").sort_index()
    if month not in table.index:
        raise ValueError(f"month {month} not in KPI table")
    prev = shift_month(month, -1)
    trailing = [shift_month(month, -i) for i in range(TRAILING_MONTHS, 0, -1)]
    trailing = [m for m in trailing if m in table.index]
    out = []
    for kpi in KPI_NAMES:
        cur = float(table.at[month, kpi])
        prv = float(table.at[prev, kpi]) if prev in table.index else float("nan")
        hist = table.loc[trailing, kpi].astype(float)
        mean, std = float(hist.mean()), float(hist.std(ddof=1))
        pct = (cur - prv) / abs(prv) if prv not in (0.0,) and math.isfinite(prv) else None
        z = (cur - mean) / std if std and math.isfinite(std) and std > 0 else None
        sig = (z is not None and abs(z) >= Z_THRESHOLD) or (
            pct is not None and abs(pct) >= PCT_THRESHOLD
        )
        direction = "up" if cur > prv else "down" if cur < prv else "flat"
        out.append(KPIChange(kpi, cur, prv, _clean(pct), _clean(z), mean, std, direction, sig))
    return out


def detect_changes(con: duckdb.DuckDBPyConnection, month: str) -> list[KPIChange]:
    """Compare every KPI in `month` with the previous month and the trailing window."""
    return detect_from_table(monthly_kpis(con), month)


def significant_changes(changes: list[KPIChange]) -> list[KPIChange]:
    """Only the flagged KPI changes."""
    return [c for c in changes if c.significant]
