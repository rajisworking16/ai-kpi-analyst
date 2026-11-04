"""KPI definitions and computation over the `orders_enriched` view.

All KPI definitions live in KPI_DEFINITIONS so the README, the LLM prompt and the
code read from one source.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import duckdb
import pandas as pd

from config import WINDOW_END, WINDOW_START

log = logging.getLogger(__name__)

KPI_DEFINITIONS: dict[str, dict[str, str]] = {
    "revenue": {
        "label": "Revenue",
        "definition": "Sum of item price for orders with status 'delivered'",
        "kind": "additive",
        "unit": "BRL",
    },
    "orders": {
        "label": "Orders",
        "definition": "Count of distinct delivered order_id",
        "kind": "additive",
        "unit": "count",
    },
    "aov": {
        "label": "AOV",
        "definition": "Revenue / Orders (average delivered order value)",
        "kind": "ratio",
        "unit": "BRL",
    },
    "freight_ratio": {
        "label": "Freight ratio",
        "definition": "Sum of freight_value / Revenue, delivered orders",
        "kind": "ratio",
        "unit": "fraction",
    },
    "avg_delivery_days": {
        "label": "Avg delivery days",
        "definition": "Mean of (delivered date - purchase timestamp) in days, delivered orders "
                      "with a delivery date",
        "kind": "rate",
        "unit": "days",
    },
    "late_rate": {
        "label": "Late delivery rate",
        "definition": "Share of delivered orders whose delivered date is after the estimated "
                      "delivery date",
        "kind": "rate",
        "unit": "fraction",
    },
    "avg_review_score": {
        "label": "Avg review score",
        "definition": "Mean review score per order, averaged over orders with a review",
        "kind": "rate",
        "unit": "score 1-5",
    },
    "cancellation_rate": {
        "label": "Cancellation rate",
        "definition": "Canceled orders / all orders placed in the period",
        "kind": "rate",
        "unit": "fraction",
    },
}

KPI_NAMES = list(KPI_DEFINITIONS)
DIMENSIONS = ["category", "customer_state", "seller_id", "payment_type"]
PERIOD_COLUMNS = {"month": "order_month", "week": "order_week"}


def _order_level_sql(dims: Sequence[str], period_col: str, where: str) -> str:
    """One row per (order, period, dims): order-level values within a segment."""
    dim_cols = "".join(f", {d}" for d in dims)
    return f"""
        SELECT order_id, {period_col} AS period{dim_cols},
            ANY_VALUE(order_status) AS order_status,
            SUM(price) AS revenue,
            SUM(freight_value) AS freight,
            ANY_VALUE(delivery_days) AS delivery_days,
            ANY_VALUE(is_late) AS is_late,
            ANY_VALUE(review_score) AS review_score
        FROM orders_enriched
        WHERE {where}
        GROUP BY order_id, {period_col}{dim_cols}
    """


def kpi_sql(dims: Sequence[str] = (), grain: str = "month", where: str = "TRUE") -> str:
    """Build SQL that returns every KPI per period (and per segment for `dims`)."""
    period_col = PERIOD_COLUMNS[grain]
    dim_cols = "".join(f", {d}" for d in dims)
    dlv = "order_status = 'delivered'"
    return f"""
        WITH o AS ({_order_level_sql(dims, period_col, where)})
        SELECT period{dim_cols},
            COALESCE(SUM(revenue) FILTER (WHERE {dlv}), 0) AS revenue,
            COUNT(*) FILTER (WHERE {dlv}) AS orders,
            SUM(revenue) FILTER (WHERE {dlv})
                / NULLIF(COUNT(*) FILTER (WHERE {dlv}), 0) AS aov,
            SUM(freight) FILTER (WHERE {dlv})
                / NULLIF(SUM(revenue) FILTER (WHERE {dlv}), 0) AS freight_ratio,
            AVG(delivery_days) FILTER (WHERE {dlv} AND delivery_days IS NOT NULL)
                AS avg_delivery_days,
            AVG(is_late) FILTER (WHERE {dlv} AND is_late IS NOT NULL) AS late_rate,
            AVG(review_score) AS avg_review_score,
            AVG(CASE WHEN order_status = 'canceled' THEN 1.0 ELSE 0.0 END) AS cancellation_rate,
            COUNT(*) AS orders_placed,
            COUNT(*) FILTER (WHERE {dlv} AND delivery_days IS NOT NULL) AS delivered_with_date,
            COUNT(*) FILTER (WHERE {dlv} AND delivery_days IS NULL) AS delivered_missing_date,
            COUNT(*) FILTER (WHERE review_score IS NOT NULL) AS orders_reviewed
        FROM o
        GROUP BY period{dim_cols}
        ORDER BY period{dim_cols}
    """


def compute_kpis(
    con: duckdb.DuckDBPyConnection,
    dims: Sequence[str] = (),
    grain: str = "month",
    start: str = WINDOW_START,
    end: str = WINDOW_END,
) -> pd.DataFrame:
    """Return a DataFrame of KPIs per period (and segment) inside the analysis window."""
    period_col = PERIOD_COLUMNS[grain]
    if grain == "month":
        where = f"order_month BETWEEN '{start}' AND '{end}'"
    else:
        where = f"order_month BETWEEN '{start}' AND '{end}' AND {period_col} IS NOT NULL"
    df = con.execute(kpi_sql(dims, grain, where)).df()
    missing = int(df["delivered_missing_date"].sum())
    if missing:
        log.info("Excluded %d delivered orders with no delivery date from delivery KPIs", missing)
    if grain == "week":
        df["period"] = df["period"].astype(str)
    return df


def monthly_kpis(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Monthly KPI totals for the analysis window."""
    return compute_kpis(con)


def definitions_markdown() -> str:
    """KPI definitions as a Markdown table (used by README and prompts)."""
    lines = ["| KPI | Column | Definition |", "|---|---|---|"]
    for key, d in KPI_DEFINITIONS.items():
        lines.append(f"| {d['label']} | `{key}` | {d['definition']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    from config import DB_PATH

    logging.basicConfig(level=logging.INFO)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    pd.set_option("display.width", 200)
    print(monthly_kpis(con)[["period", *KPI_NAMES, "delivered_missing_date"]].round(3))
