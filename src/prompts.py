"""All LLM prompts in one place. Bump PROMPT_VERSION whenever a prompt changes."""

from __future__ import annotations

from src.kpis import definitions_markdown

PROMPT_VERSION = "v3"

SCHEMA_TEXT = """\
Main view `orders_enriched` (one row per order item; orders with no items have NULL item
fields). Columns:
- order_id VARCHAR, order_item_id BIGINT, order_status VARCHAR ('delivered', 'canceled',
  'shipped', ...)
- order_purchase_timestamp TIMESTAMP, order_month VARCHAR ('YYYY-MM'), order_week DATE
- order_delivered_customer_date TIMESTAMP, order_estimated_delivery_date TIMESTAMP
- delivery_days DOUBLE (purchase to delivery), is_late INTEGER (1 = delivered after estimate)
- customer_id, customer_unique_id, customer_state (2-letter code, e.g. 'SP'), customer_city
- seller_id VARCHAR, seller_state VARCHAR, product_id VARCHAR
- category VARCHAR (English category name), category_pt VARCHAR (Portuguese name)
- price DOUBLE (item price), freight_value DOUBLE (item freight)
- payment_type VARCHAR (order's main payment type: credit_card, boleto, voucher, debit_card)
- payment_value DOUBLE (order total paid), review_score DOUBLE (order's average review 1-5)

Other tables: orders, order_items, payments(order_id, payment_sequential, payment_type,
payment_installments, payment_value), reviews(review_id, order_id, review_score),
customers, sellers, products.

Rules for correct SQL:
- Order-level values (delivery_days, is_late, review_score, payment_value) repeat on every
  item row, so aggregate them per order first or use COUNT(DISTINCT order_id).
- Revenue = SUM(price) over delivered orders. Orders = COUNT(DISTINCT order_id) over
  delivered orders.
- Filter months with order_month, e.g. WHERE order_month IN ('2018-04', '2018-05').
"""

def sql_templates(month: str, prev: str) -> str:
    """Copyable SQL templates with the real months filled in."""
    return f"""\
SQL template for an additive KPI by segment (change dimension, KPI and filters as needed):
WITH m AS (
  SELECT customer_state AS segment,
         SUM(price) FILTER (WHERE order_month = '{prev}') AS prev,
         SUM(price) FILTER (WHERE order_month = '{month}') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('{prev}', '{month}')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m ORDER BY abs(change) DESC LIMIT 10

SQL template for a per-order rate KPI by segment (is_late, delivery_days, review_score):
WITH o AS (
  SELECT DISTINCT order_id, order_month, customer_state AS segment, is_late
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('{prev}', '{month}'))
SELECT segment,
       AVG(is_late) FILTER (WHERE order_month = '{prev}') AS rate_prev,
       AVG(is_late) FILTER (WHERE order_month = '{month}') AS rate_curr,
       COUNT(*) FILTER (WHERE order_month = '{month}') AS orders_curr
FROM o GROUP BY 1 ORDER BY orders_curr DESC LIMIT 10"""


REPORT_RULES = """\
Report rules:
- Order findings by how much of the KPI change they explain, largest first. The first
  finding must be the main root cause.
- Each finding names one dimension (category, customer_state, seller_id, payment_type, or
  overall) and one segment value copied exactly from the data (e.g. 'SP', 'health_beauty',
  a full seller_id). Use segment 'all' with dimension 'overall' for broad effects.
- If the change is spread across many segments with no single driver, say the change is
  broad-based in the summary and do not claim that one segment explains most of it.
- Every number in `numbers`, `claim` and `summary` must be copied from a table or query
  result you were given. Do not compute new numbers. Fractions may be written as
  percentages (0.23 -> 23%).
- `evidence_query_ids` lists the ids of the tables or queries that contain those numbers,
  e.g. "decomp_revenue_category" or "q_1a2b3c".
- Give 1 to 4 findings and 2 to 4 investigate_next items. summary is 2 to 4 sentences.
"""

AGENT_SYSTEM = f"""\
You are a careful data analyst. You explain why business KPIs changed in an e-commerce
marketplace (Olist, Brazil, amounts in BRL). You have deterministic change detection and
driver decomposition tables, and you can run read-only DuckDB SQL to test hypotheses.

KPI definitions:
{definitions_markdown()}

Database schema:
{SCHEMA_TEXT}
You work in steps. Each step you return one JSON action:
- run_sql: test one hypothesis with one SELECT query (set hypothesis_id, reason, sql).
- update_hypothesis: set status supported, rejected or inconclusive for one hypothesis, citing
  the query ids that justify it in evidence_query_ids.
- final_report: when every hypothesis has a status, or you have enough evidence.
Unused fields: sql = "", status = "none", evidence_query_ids = [].
Only SELECT or WITH queries are allowed; results are limited to 200 rows. Aggregate in SQL.
"""


def hypotheses_prompt(question: str, month: str, prev: str, facts: str,
                      context_md: str) -> str:
    return f"""\
Question: {question}
Target month: {month}, compared with the previous month {prev}.

Facts (computed, trust these):
{facts}

{context_md}

{sql_templates(month, prev)}

Propose 3 to 5 hypotheses that could explain the change asked about. Base them on the
facts and decomposition tables above: name the dimension and segment each hypothesis is about.
Include at least one alternative explanation (for example a broad, overall change).
Return JSON with a `hypotheses` list (ids H1, H2, ...)."""


def step_prompt(status_lines: str, steps_left: int, query_ids: str) -> str:
    return f"""\
Hypothesis status:
{status_lines}
Queries run so far (cite these exact ids): {query_ids or "none"}
Steps left: {steps_left}. Choose the next action (run_sql, update_hypothesis or
final_report). Test open hypotheses one at a time; after a query answers a hypothesis,
update it and cite the query id. Compare the target month with the previous month in SQL."""


def sql_result_message(query_id: str, sql: str, result_md: str, error: str | None) -> str:
    if error:
        return f"Query {query_id} failed: {error}\nFix the SQL or test something else."
    return f"Result of {query_id}:\n{result_md}"


FINAL_REPORT_PROMPT = f"""\
Write the final report now as JSON with summary, findings and investigate_next.
{REPORT_RULES}"""


def revision_prompt(unsupported_md: str, evidence_md: str) -> str:
    return f"""\
A verifier checked every number in your report against the tables and query results. These
numbers were not found in the cited evidence:
{unsupported_md}

Cited evidence:
{evidence_md}

Return a corrected report as JSON with the same schema. Replace each unsupported number with
the exact value from the evidence, or remove it. Keep everything else that was correct.
{REPORT_RULES}"""


BASELINE_SYSTEM = f"""\
You are a data analyst. You explain why business KPIs changed in an e-commerce marketplace
(Olist, Brazil, amounts in BRL).

KPI definitions:
{definitions_markdown()}
"""


def baseline_prompt(question: str, month: str, kpi_md: str) -> str:
    return f"""\
Question: {question}
Target month: {month} (compared with the previous month).

{kpi_md}

Answer with a report as JSON with summary, findings and investigate_next.
{REPORT_RULES}"""
