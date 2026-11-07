# KPI analysis: Why did AOV rise?

- Month: 2018-05  
- Mode: agent  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s02_category_price_hike.duckdb`  
- Steps: 9, wall time: 120.3s  
- Unsupported claim rate: 0.0% (0/3 numbers)

## Summary

The increase in AOV in 2018-05 compared to 2018-04 is primarily driven by a significant rise in the average order value for customers in the state of São Paulo (SP) and a shift towards the 'boleto' payment method, which has a higher average order value. Additionally, the introduction of higher-priced items in the 'watches_gifts' category also contributed to the increase.

## Findings

### 1. The state of São Paulo (SP) had the largest excess_share of 1.0357, indicating a significant increase in AOV for SP customers.

🟡 partially verified · KPI `aov` · customer_state = `SP` · confidence high

- 1.04: excess_share
- Evidence: `decomp_aov_customer_state`, `q_a3d9fa`, `q_3db04d`, `q_3a01c5`, `decomp_revenue_category`

### 2. The 'boleto' payment method had the highest contribution to the change in AOV, with a contribution of 1.0841, indicating a significant shift towards this payment method.

🟢 verified · KPI `aov` · payment_type = `boleto` · confidence high

- 1.08: contribution
- Evidence: `decomp_aov_payment_type`, `q_3a01c5`

### 3. The 'watches_gifts' category had the highest contribution to the change in AOV, with a contribution of 4.5972, indicating a significant increase in the average order value for this category.

🟢 verified · KPI `aov` · category = `watches_gifts` · confidence high

- 4.60: contribution
- Evidence: `decomp_aov_category`, `q_3db04d`

## Investigate next

- **Explore the specific products within the 'watches_gifts' category that contributed most to the increase in AOV.**: Identify if certain products or subcategories drove the increase in AOV for this category. (data needed: Detailed product-level data within the 'watches_gifts' category.)
- **Analyze the customer behavior and purchasing patterns in São Paulo (SP) to understand the factors driving the increase in AOV.**: Identify if there are specific customer segments or behaviors that contributed to the increase in AOV for SP. (data needed: Customer-level data including purchase history and customer demographics.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The increase in AOV is driven by a significant rise in the average order value for customers in the state of São Paulo (SP). |
| H2 | supported | The introduction of higher-priced items in the 'watches_gifts' category has contributed to the increase in AOV. |
| H3 | supported | The increase in AOV is due to a shift towards the 'boleto' payment method, which has a higher average order value. |
| H4 | inconclusive | There has been a general increase in the average order value across all segments, which could be due to broader market factors. |

## Evidence queries

**`q_a3d9fa`** (H1, 1 rows)

```sql
WITH m AS (
  SELECT customer_state AS segment,
         AVG(price) FILTER (WHERE order_month = '2018-04') AS prev_aov,
         AVG(price) FILTER (WHERE order_month = '2018-05') AS curr_aov
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND customer_state = 'SP'
  GROUP BY 1)
SELECT segment, prev_aov, curr_aov, curr_aov - prev_aov AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev_aov | curr_aov | change |
|---|---|---|---|
| SP | 112.17 | 120.46 | 8.2891 |

**`q_3db04d`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT category AS segment,
         AVG(price) FILTER (WHERE order_month = '2018-04') AS prev_aov,
         AVG(price) FILTER (WHERE order_month = '2018-05') AS curr_aov
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND category = 'watches_gifts'
  GROUP BY 1)
SELECT segment, prev_aov, curr_aov, curr_aov - prev_aov AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev_aov | curr_aov | change |
|---|---|---|---|
| watches_gifts | 179.40 | 190.98 | 11.585 |

**`q_3a01c5`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         AVG(price) FILTER (WHERE order_month = '2018-04') AS prev_aov,
         AVG(price) FILTER (WHERE order_month = '2018-05') AS curr_aov
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05') AND payment_type = 'boleto'
  GROUP BY 1)
SELECT segment, prev_aov, curr_aov, curr_aov - prev_aov AS change FROM m ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev_aov | curr_aov | change |
|---|---|---|---|
| boleto | 106.92 | 112.82 | 5.9033 |

