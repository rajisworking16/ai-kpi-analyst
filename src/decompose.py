"""Deterministic driver decomposition of KPI changes between two months."""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from config import TOP_SEGMENTS
from src.detect import shift_month
from src.kpis import DIMENSIONS, KPI_DEFINITIONS, compute_kpis

# Volume base used to weight each segment for non-additive KPIs.
WEIGHT_COLUMN = {
    "aov": "orders",
    "freight_ratio": "revenue",
    "avg_delivery_days": "delivered_with_date",
    "late_rate": "delivered_with_date",
    "avg_review_score": "orders_reviewed",
    "cancellation_rate": "orders_placed",
}


def revenue_split(orders0: float, aov0: float, orders1: float, aov1: float) -> dict[str, float]:
    """Split revenue change into volume, AOV and interaction effects (sums exactly)."""
    d_orders, d_aov = orders1 - orders0, aov1 - aov0
    split = {
        "revenue_prev": orders0 * aov0,
        "revenue_curr": orders1 * aov1,
        "volume_effect": d_orders * aov0,
        "aov_effect": d_aov * orders0,
        "interaction": d_orders * d_aov,
    }
    split["total_change"] = split["revenue_curr"] - split["revenue_prev"]
    return split


def _pivot(seg: pd.DataFrame, dim: str, prev: str, month: str, cols: list[str]) -> pd.DataFrame:
    seg = seg.copy()
    seg[dim] = seg[dim].fillna("unknown").astype(str)
    p0 = seg[seg["period"] == prev].set_index(dim)[cols]
    p1 = seg[seg["period"] == month].set_index(dim)[cols]
    return pd.merge(p0, p1, how="outer", left_index=True, right_index=True,
                    suffixes=("_0", "_1"))


def additive_contribution(seg: pd.DataFrame, dim: str, kpi: str, prev: str, month: str
                          ) -> pd.DataFrame:
    """Per-segment change of an additive KPI and its share of the total change."""
    t = _pivot(seg, dim, prev, month, [kpi]).fillna(0.0)
    out = pd.DataFrame({"segment": t.index, "value_prev": t[f"{kpi}_0"],
                        "value_curr": t[f"{kpi}_1"]}).reset_index(drop=True)
    out["change"] = out["value_curr"] - out["value_prev"]
    total = out["change"].sum()
    out["share_of_change"] = out["change"] / total if total else np.nan
    out["contribution"] = out["change"]
    prev_total = out["value_prev"].sum()
    out["volume_share"] = out["value_prev"] / prev_total if prev_total else np.nan
    return _add_excess(out, total)


def _add_excess(out: pd.DataFrame, total: float) -> pd.DataFrame:
    """Contribution beyond what the segment's prior size predicts.

    If a change were spread evenly, every segment would contribute volume_share * total and
    its excess would be ~0. A concentrated cause shows up as a large excess.
    """
    out["excess_contribution"] = out["contribution"] - out["volume_share"] * total
    out["excess_share"] = out["excess_contribution"] / total if total else np.nan
    return out


def rate_contribution(seg: pd.DataFrame, dim: str, kpi: str, prev: str, month: str
                      ) -> pd.DataFrame:
    """Shift-share split of a rate/ratio KPI into within-segment rate and mix effects.

    With volume shares w and segment rates r, the change in the weighted mean is
    sum(w1*r1 - w0*r0) = sum(rate_effect + mix_effect), where
    rate_effect = (w0+w1)/2 * (r1-r0) and mix_effect = (w1-w0) * (r0+r1)/2.
    """
    wcol = WEIGHT_COLUMN[kpi]
    t = _pivot(seg, dim, prev, month, [kpi, wcol])
    w0 = t[f"{wcol}_0"].fillna(0.0)
    w1 = t[f"{wcol}_1"].fillna(0.0)
    r0, r1 = t[f"{kpi}_0"].astype(float), t[f"{kpi}_1"].astype(float)
    r0 = r0.where(w0 > 0, r1).fillna(0.0)
    r1 = r1.where(w1 > 0, r0).fillna(0.0)
    s0, s1 = w0 / w0.sum(), w1 / w1.sum()
    out = pd.DataFrame({
        "segment": t.index, "value_prev": r0.values, "value_curr": r1.values,
        "weight_prev": s0.values, "weight_curr": s1.values,
        "volume_prev": w0.values, "volume_curr": w1.values,
    })
    out["change"] = out["value_curr"] - out["value_prev"]
    out["rate_effect"] = (out["weight_prev"] + out["weight_curr"]) / 2 * out["change"]
    out["mix_effect"] = (out["weight_curr"] - out["weight_prev"]) * (
        out["value_prev"] + out["value_curr"]) / 2
    out["contribution"] = out["rate_effect"] + out["mix_effect"]
    total = out["contribution"].sum()
    out["share_of_change"] = out["contribution"] / total if total else np.nan
    out["volume_share"] = out["weight_prev"]
    return _add_excess(out, total)


def top_excess_driver(df: pd.DataFrame) -> pd.Series | None:
    """Row with the largest absolute excess contribution, or None for an empty table."""
    if df.empty:
        return None
    return df.loc[df["excess_contribution"].abs().idxmax()]


def segment_contribution(seg: pd.DataFrame, dim: str, kpi: str, prev: str, month: str,
                         top: int = TOP_SEGMENTS) -> pd.DataFrame:
    """Top `top` segments of `dim` by absolute contribution to the change in `kpi`."""
    if KPI_DEFINITIONS[kpi]["kind"] == "additive":
        out = additive_contribution(seg, dim, kpi, prev, month)
    else:
        out = rate_contribution(seg, dim, kpi, prev, month)
    out = out.reindex(out["contribution"].abs().sort_values(ascending=False).index)
    return out.head(top).reset_index(drop=True)


def decompose(con: duckdb.DuckDBPyConnection, month: str, kpis: list[str],
              dims: list[str] | None = None, top: int = TOP_SEGMENTS) -> dict:
    """Revenue split plus per-dimension segment contributions for each KPI in `kpis`."""
    prev = shift_month(month, -1)
    dims = dims or DIMENSIONS
    totals = compute_kpis(con, start=prev, end=month).set_index("period")
    split = revenue_split(float(totals.at[prev, "orders"]), float(totals.at[prev, "aov"]),
                          float(totals.at[month, "orders"]), float(totals.at[month, "aov"]))
    segments: dict[str, dict[str, pd.DataFrame]] = {k: {} for k in kpis}
    for dim in dims:
        seg = compute_kpis(con, dims=[dim], start=prev, end=month)
        for kpi in kpis:
            segments[kpi][dim] = segment_contribution(seg, dim, kpi, prev, month, top)
    return {"month": month, "previous_month": prev, "revenue_split": split,
            "segments": segments}
