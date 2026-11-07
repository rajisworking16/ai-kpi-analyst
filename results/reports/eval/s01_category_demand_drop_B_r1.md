# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: agent  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s01_category_demand_drop.duckdb`  
- Steps: 11, wall time: 321.3s  
- Unsupported claim rate: 0.0% (0/6 numbers)

## Summary

The decline in revenue is primarily driven by a significant drop in sales of the 'health_beauty' category, followed by a decline in sales from the 'PR' state, and an overall decrease in the number of orders. These factors collectively explain the majority of the revenue decline.

## Findings

### 1. The 'health_beauty' category contributed the most to the revenue decline, with a significant drop in sales.

🟢 verified · KPI `revenue` · category = `health_beauty` · confidence high

- -69,497.75: revenue contribution change
- 0.8955: excess share
- Evidence: `decomp_revenue_category`, `q_0bc12b`, `q_6ca933`, `q_64e175`, `decomp_revenue_category`

### 2. Sales from the 'PR' state declined significantly, contributing to the revenue drop.

🟢 verified · KPI `revenue` · customer_state = `PR` · confidence high

- -23,058.93: revenue contribution change
- 0.2605: excess share
- Evidence: `decomp_revenue_customer_state`, `q_a2f58e`

### 3. There was an overall decline in the number of orders, which also contributed to the revenue drop.

🟢 verified · KPI `orders` · overall = `all` · confidence high

- -550.00: change in orders
- -0.0809: percentage change in orders
- Evidence: `q_64e175`

## Investigate next

- **Investigate the specific products or items within the 'health_beauty' category that contributed most to the decline in sales.**: To identify specific products that may need targeted marketing or pricing adjustments. (data needed: Sales data by product within the 'health_beauty' category.)
- **Analyze the reasons behind the decline in sales from the 'PR' state.**: To understand if there are specific issues in the 'PR' state that need addressing, such as local market trends or customer preferences. (data needed: Customer feedback, market trends, and local economic indicators for the 'PR' state.)
- **Explore the reasons for the overall decline in orders.**: To determine if there are broader market or operational factors affecting order volume. (data needed: Market trends, customer satisfaction surveys, and operational metrics.)
- **Review payment methods and customer behavior trends.**: To ensure that the shift in payment methods is not indicative of a broader issue with customer payment preferences or trust. (data needed: Payment method usage trends and customer feedback on payment experiences.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The decline in revenue is primarily driven by a significant drop in sales of the 'health_beauty' category. |
| H2 | supported | The decrease in revenue is due to a shift in customer behavior, specifically a decline in sales from the 'PR' state. |
| H3 | supported | The revenue decline is partially due to a shift in payment methods, with a significant drop in sales through 'boleto' payments. |
| H4 | supported | There is an overall decline in the number of orders, which is contributing to the revenue drop. |
| H5 | supported | The decline in revenue is due to a combination of factors, including a drop in sales of the 'health_beauty' category and a shift in customer behavior in the 'PR' state. |

## Evidence queries

**`q_0bc12b`** (H1, 1 rows)

```sql
WITH m AS (
  SELECT category AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'health_beauty' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| health_beauty | 91058.45 | 21560.70 | -69497.75 |

**`q_a2f58e`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT customer_state AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'PR' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| PR | 65914.88 | 42855.95 | -23058.93 |

**`q_6ca933`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'boleto' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| boleto | 160595.75 | 152631.69 | -7964.06 |

**`q_64e175`** (H4, 1 rows)

```sql
WITH m AS (
  SELECT COUNT(DISTINCT order_id) FILTER (WHERE order_month = '2018-04') AS prev_orders,
         COUNT(DISTINCT order_id) FILTER (WHERE order_month = '2018-05') AS curr_orders
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05'))
SELECT prev_orders, curr_orders, curr_orders - prev_orders AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| prev_orders | curr_orders | change |
|---|---|---|
| 6798 | 6248 | -550 |

