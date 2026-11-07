# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: agent  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s12_decoy_broad_drop.duckdb`  
- Steps: 11, wall time: 217.1s  
- Unsupported claim rate: 0.0% (0/9 numbers)

## Summary

The revenue drop in 2018-05 was primarily due to a broad decline in the use of credit cards as the main payment method, followed by a decrease in the average order value for the 'baby' category. The state of SP also saw a significant decrease in revenue, but this was mainly due to a decrease in the volume of orders.

## Findings

### 1. The overall decrease in revenue is due to a broad decline in the use of credit cards as the main payment method.

🟡 partially verified · KPI `revenue` · payment_type = `credit_card` · confidence high

- -128,454.01: revenue change
- 0.8132: volume share
- 0.0057: excess share
- Evidence: `q_b724b9`, `decomp_revenue_payment_type`, `revenue_split`, `kpi_changes_2018-05_vs_2018-04`, `decomp_revenue_category`

### 2. The revenue drop is mainly due to a decline in the average order value (AOV) for the 'baby' category.

🟡 partially verified · KPI `revenue` · category = `baby` · confidence high

- -18,025.37: revenue change
- 0.0917: volume share
- 0.0656: excess share
- Evidence: `q_935457`, `decomp_revenue_category`, `revenue_split`, `kpi_changes_2018-05_vs_2018-04`

### 3. The revenue drop in SP (customer_state) is primarily due to a decrease in the volume of orders.

🟡 partially verified · KPI `revenue` · customer_state = `SP` · confidence high

- -32,861.21: revenue change
- 0.4019: volume share
- -0.1939: excess share
- Evidence: `q_066434`, `decomp_revenue_customer_state`, `revenue_split`, `kpi_changes_2018-05_vs_2018-04`

## Investigate next

- **Explore the reasons behind the decline in the use of credit cards as the main payment method.**: Identify if there were any changes in credit card policies, customer preferences, or external factors affecting credit card usage. (data needed: Credit card usage trends, customer feedback, and any relevant policy changes.)
- **Analyze the 'baby' category to understand the factors contributing to the decline in average order value.**: Identify if there were any specific product issues, pricing changes, or market trends affecting this category. (data needed: Product performance data, pricing history, and market trend analysis.)
- **Investigate the reasons for the decrease in the volume of orders in SP.**: Identify if there were any regional economic or market factors affecting the state of SP. (data needed: Regional economic indicators, market trends, and customer feedback.)
- **Review the overall revenue trends to identify any broader market or economic factors affecting the entire marketplace.**: Identify if there were any external factors, such as economic downturns or market shifts, impacting the overall revenue. (data needed: Market trend analysis, economic indicators, and competitor performance data.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The revenue drop in SP (customer_state) is primarily due to a decrease in the volume of orders. |
| H2 | supported | The revenue drop is mainly due to a decline in the average order value (AOV) for the 'baby' category. |
| H3 | rejected | The revenue drop is largely due to a decrease in the volume of orders from the '2eb70248d66e0e3ef83659f71b244378' seller. |
| H4 | supported | The overall decrease in revenue is due to a broad decline in the use of credit cards as the main payment method. |
| H5 | rejected | The revenue drop is not due to a significant change in any specific dimension, but rather a combination of small changes across multiple dimensions. |

## Evidence queries

**`q_066434`** (H1, 1 rows)

```sql
WITH m AS (
  SELECT customer_state AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'SP' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| SP | 391246.99 | 358385.78 | -32861.21 |

**`q_935457`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT category AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev_revenue,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr_revenue,
         AVG(price) FILTER (WHERE order_month = '2018-04') AS prev_aov,
         AVG(price) FILTER (WHERE order_month = '2018-05') AS curr_aov
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev_revenue, curr_revenue, curr_revenue - prev_revenue AS revenue_change, curr_aov, prev_aov, curr_aov - prev_aov AS aov_change FROM m WHERE segment = 'baby' ORDER BY abs(revenue_change) DESC LIMIT 10;
```

| segment | prev_revenue | curr_revenue | revenue_change | curr_aov | prev_aov | aov_change |
|---|---|---|---|---|---|---|
| baby | 47201.22 | 29175.85 | -18025.37 | 136.98 | 199.16 | -62.1854 |

**`q_7e69fe`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT seller_id AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = '2eb70248d66e0e3ef83659f71b244378' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| 2eb70248d66e0e3ef83659f71b244378 | 3245.40 | 10853.30 | 7607.90 |

**`q_b724b9`** (H4, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'credit_card' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| credit_card | 786086.91 | 657632.90 | -128454.01 |

