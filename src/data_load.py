"""Load the raw Olist CSVs into DuckDB and build the `orders_enriched` view."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from config import DB_PATH, RAW_DIR

TABLE_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

TIMESTAMP_COLUMNS = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# One row per order item. Orders without items (mostly canceled/unavailable) are kept
# with NULL item fields so cancellation rate can be computed from the same view.
# payment_type is the order's primary payment type (largest total payment value).
ORDERS_ENRICHED_SQL = """
CREATE OR REPLACE VIEW orders_enriched AS
WITH review_by_order AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM reviews GROUP BY order_id
),
pay_by_type AS (
    SELECT order_id, payment_type, SUM(payment_value) AS v
    FROM payments GROUP BY order_id, payment_type
),
primary_payment AS (
    SELECT order_id, arg_max(payment_type, v) AS payment_type, SUM(v) AS payment_value
    FROM pay_by_type GROUP BY order_id
)
SELECT
    o.order_id,
    i.order_item_id,
    o.order_status,
    o.order_purchase_timestamp,
    strftime(o.order_purchase_timestamp, '%Y-%m') AS order_month,
    CAST(date_trunc('week', o.order_purchase_timestamp) AS DATE) AS order_week,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    date_diff('second', o.order_purchase_timestamp, o.order_delivered_customer_date)
        / 86400.0 AS delivery_days,
    CASE WHEN o.order_delivered_customer_date IS NULL THEN NULL
         WHEN CAST(o.order_delivered_customer_date AS DATE)
              > CAST(o.order_estimated_delivery_date AS DATE) THEN 1 ELSE 0 END AS is_late,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    c.customer_city,
    i.seller_id,
    s.seller_state,
    i.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    COALESCE(p.product_category_name, 'unknown') AS category_pt,
    i.price,
    i.freight_value,
    pp.payment_type,
    pp.payment_value,
    r.review_score
FROM orders o
LEFT JOIN order_items i ON i.order_id = o.order_id
LEFT JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN sellers s ON s.seller_id = i.seller_id
LEFT JOIN products p ON p.product_id = i.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
LEFT JOIN review_by_order r ON r.order_id = o.order_id
LEFT JOIN primary_payment pp ON pp.order_id = o.order_id
"""


def _load_table(con: duckdb.DuckDBPyConnection, table: str, path: Path) -> None:
    con.execute(
        f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?, header=true)",
        [str(path)],
    )
    for col in TIMESTAMP_COLUMNS.get(table, []):
        con.execute(
            f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TIMESTAMP USING CAST({col} AS TIMESTAMP)"
        )


def create_views(con: duckdb.DuckDBPyConnection) -> None:
    """(Re)create derived views. Safe to call after tables are modified."""
    con.execute(ORDERS_ENRICHED_SQL)


def build_database(raw_dir: Path = RAW_DIR, db_path: Path = DB_PATH) -> Path:
    """Build the DuckDB database from raw CSVs. Idempotent: tables are replaced."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        for table, fname in TABLE_FILES.items():
            _load_table(con, table, raw_dir / fname)
        create_views(con)
    finally:
        con.close()
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    path = build_database(args.raw, args.db)
    con = duckdb.connect(str(path), read_only=True)
    for table in [*TABLE_FILES, "orders_enriched"]:
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:22s} {n:>8,d}")
    con.close()


if __name__ == "__main__":
    main()
