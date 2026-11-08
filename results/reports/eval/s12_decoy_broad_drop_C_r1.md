# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s12_decoy_broad_drop.duckdb`  
- Steps: 10, wall time: 153.3s  
- Unsupported claim rate: 0.0% (0/6 numbers)

## Summary

The revenue drop in 2018-05 compared to 2018-04 is primarily due to a decrease in the volume of orders in SP, followed by a decline in the average order value for the 'baby' category, and a shift in payment methods, specifically a decrease in credit card usage. These factors collectively explain the overall revenue decline.

## Findings

### 1. The revenue drop is mainly due to a decrease in the volume of orders in SP.

🟢 verified · KPI `revenue` · customer_state = `SP` · confidence high

- -32,861.21: contribution to revenue change
- -0.1939: excess share
- Evidence: `decomp_revenue_customer_state`, `q_f7eae7`

### 2. The revenue drop is due to a decline in the average order value for the 'baby' category.

🟢 verified · KPI `revenue` · category = `baby` · confidence high

- -18,025.37: contribution to revenue change
- 0.0656: excess share
- Evidence: `decomp_revenue_category`, `q_e0c55a`

### 3. The revenue drop is due to a shift in payment methods, specifically a decrease in credit card usage.

🟢 verified · KPI `revenue` · payment_type = `credit_card` · confidence high

- -128,454.01: contribution to revenue change
- -0.0076: excess share
- Evidence: `decomp_revenue_payment_type`, `q_720bec`

## Investigate next

- **Explore the specific reasons behind the decrease in orders in SP, such as marketing campaigns or local economic factors.**: Understanding the root cause can help in formulating targeted strategies to mitigate the impact. (data needed: Customer feedback, local market trends, and marketing campaign data.)
- **Analyze the 'baby' category to identify specific products or subcategories that are driving the decline in average order value.**: This can help in making informed decisions about product pricing and marketing. (data needed: Detailed product-level sales data and customer reviews.)
- **Investigate the reasons for the shift in payment methods, particularly the decrease in credit card usage.**: Understanding the customer preferences and market trends can help in adjusting payment options. (data needed: Customer payment preference surveys and payment method usage trends.)
- **Monitor overall e-commerce trends in the broader market to understand if the decline is part of a larger market trend.**: This can provide context and help in making strategic decisions. (data needed: Market research reports and industry analysis.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The revenue drop in SP (customer_state) is primarily due to a decrease in the volume of orders. |
| H2 | supported | The revenue drop is mainly due to a decline in the average order value (AOV) for the 'baby' category. |
| H3 | supported | The revenue drop is due to a shift in payment methods, specifically a decrease in credit card usage. |
| H4 | supported | The revenue drop is a result of a general decrease in overall e-commerce activity in the market. |

## Evidence queries

**`q_f7eae7`** (H1, 1 rows)

```sql
WITH m AS (
  SELECT customer_state AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND customer_state = 'SP'
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| SP | 391246.99 | 358385.78 | -32861.21 |

**`q_e0c55a`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT category AS segment,
         AVG(price) FILTER (WHERE order_month = '2018-04') AS prev_aov,
         AVG(price) FILTER (WHERE order_month = '2018-05') AS curr_aov
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND category = 'baby'
  GROUP BY 1)
SELECT segment, prev_aov, curr_aov, curr_aov - prev_aov AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev_aov | curr_aov | change |
|---|---|---|---|
| baby | 199.16 | 136.98 | -62.1854 |

**`q_720bec`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND payment_type = 'credit_card'
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| credit_card | 786086.91 | 657632.90 | -128454.01 |

**`q_608c3a`** (H4, 2 rows)

```sql
WITH m AS (
  SELECT order_month,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT order_month, prev, curr, curr - prev AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| order_month | prev | curr | change |
|---|---|---|---|
| 2018-04 | 973534.09 |  |  |
| 2018-05 |  | 815571.61 |  |

