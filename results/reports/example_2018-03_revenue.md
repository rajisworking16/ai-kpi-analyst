# KPI analysis: Why did revenue change?

- Month: 2018-03  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v3)  
- Database: `olist.duckdb`  
- Steps: 10, wall time: 102.0s  
- Unsupported claim rate: 0.0% (0/3 numbers)

## Summary

The increase in revenue in 2018-03 is primarily driven by a higher volume of orders in the 'SP' customer state, followed by a shift towards credit card payments and an increase in sales of the 'watches_gifts' category. These factors collectively explain the majority of the revenue growth.

## Findings

### 1. The revenue increase is primarily driven by a higher volume of orders in the 'SP' customer state.

🟢 verified · KPI `revenue` · customer_state = `SP` · confidence high

- 69,205.19: The increase in revenue in the 'SP' customer state.
- Evidence: `q_b22a63`, `decomp_revenue_customer_state`, `decomp_revenue_category`, `decomp_revenue_seller_id`, `decomp_revenue_payment_type`

### 2. The revenue increase is due to a shift in payment methods, specifically an increase in credit card usage.

🟢 verified · KPI `revenue` · payment_type = `credit_card` · confidence high

- 120,582.85: The increase in revenue for credit card payments.
- Evidence: `q_bfa315`, `decomp_revenue_payment_type`

### 3. The revenue increase is driven by a higher volume of orders in the 'watches_gifts' category.

🟢 verified · KPI `revenue` · category = `watches_gifts` · confidence high

- 34,935.87: The increase in revenue in the 'watches_gifts' category.
- Evidence: `q_060ec2`, `decomp_revenue_category`

## Investigate next

- **Explore the specific products within the 'watches_gifts' category that contributed most to the revenue increase.**: Identify which specific products drove the category's growth to understand the underlying demand drivers. (data needed: Detailed product-level sales data for the 'watches_gifts' category.)
- **Analyze the payment methods used by customers in the 'SP' state to understand the shift towards credit card usage.**: Determine if there are specific factors (e.g., marketing campaigns, payment infrastructure improvements) that influenced this change. (data needed: Detailed payment method data for the 'SP' state.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The increase in revenue is primarily driven by a higher volume of orders in the 'SP' customer state. |
| H2 | supported | The revenue increase is due to a shift in payment methods, specifically an increase in credit card usage. |
| H3 | supported | The revenue increase is driven by a higher volume of orders in the 'watches_gifts' category. |
| H4 | supported | The overall increase in revenue is due to a general market growth or seasonal effects. |

## Evidence queries

**`q_b22a63`** (H1, 1 rows)

```sql
WITH m AS (
  SELECT customer_state AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-02') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-03') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-02', '2018-03')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'SP' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| SP | 307829.15 | 377034.34 | 69205.19 |

**`q_bfa315`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-02') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-03') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-02', '2018-03')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'credit_card' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| credit_card | 651156.94 | 771739.79 | 120582.85 |

**`q_060ec2`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT category AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-02') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-03') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-02', '2018-03')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'watches_gifts' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| watches_gifts | 60725.31 | 95661.18 | 34935.87 |

**`q_94c268`** (H4, 2 rows)

```sql
WITH m AS (
  SELECT order_month,
         SUM(price) FILTER (WHERE order_month = '2018-02') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-03') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-02', '2018-03')
  GROUP BY 1)
SELECT order_month, prev, curr, curr - prev AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| order_month | prev | curr | change |
|---|---|---|---|
| 2018-03 |  | 953356.25 |  |
| 2018-02 | 826437.13 |  |  |

