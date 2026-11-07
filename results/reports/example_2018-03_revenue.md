# KPI analysis: Why did revenue change?

- Month: 2018-03  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v4)  
- Database: `olist.duckdb`  
- Steps: 11, wall time: 132.5s  
- Unsupported claim rate: 0.0% (0/9 numbers)

## Summary

The increase in revenue in 2018-03 compared to 2018-02 is primarily driven by the SP customer state, followed by a significant shift in payment methods towards credit cards, and a substantial contribution from the watches_gifts category. These factors collectively explain the majority of the revenue growth, with the SP customer state contributing the most.

## Findings

### 1. The SP customer state contributed the most to the revenue increase, with a significant excess share of 17.28%.

🟢 verified · KPI `revenue` · customer_state = `SP` · confidence high

- 69,205.19: Revenue contribution from SP in 2018-03
- 0.1728: Excess share of SP's contribution
- Evidence: `decomp_revenue_customer_state`, `q_b22a63`, `q_ae6555`, `q_060ec2`, `decomp_revenue_category`

### 2. The shift towards credit card payments significantly contributed to the revenue increase, with a large excess share of 16.22%.

🟢 verified · KPI `revenue` · payment_type = `credit_card` · confidence high

- 120,582.85: Revenue contribution from credit cards in 2018-03
- 0.1622: Excess share of credit cards' contribution
- Evidence: `decomp_revenue_payment_type`, `q_bfa315`

### 3. The watches_gifts category significantly contributed to the revenue increase, with a large excess share of 20.18%.

🟢 verified · KPI `revenue` · category = `watches_gifts` · confidence high

- 34,935.87: Revenue contribution from watches_gifts in 2018-03
- 0.2018: Excess share of watches_gifts' contribution
- Evidence: `decomp_revenue_category`, `q_060ec2`

## Investigate next

- **Analyze the specific products within the watches_gifts category that drove the revenue increase.**: Identify which products or subcategories contributed the most to the revenue growth in the watches_gifts category. (data needed: Detailed product-level data within the watches_gifts category.)
- **Examine the marketing and promotional activities in the SP region during 2018-03.**: Determine if any specific marketing campaigns or promotions in SP significantly contributed to the revenue increase. (data needed: Marketing campaign data and customer engagement metrics for the SP region.)
- **Review the payment terms and conditions for credit card payments.**: Assess if any changes in payment terms or promotions for credit cards influenced the shift in payment methods. (data needed: Payment terms and conditions for credit cards, including any promotional offers or changes.)
- **Explore the delivery logistics and customer service in the SP region.**: Identify if any improvements in delivery logistics or customer service in SP contributed to the increase in customer satisfaction and revenue. (data needed: Delivery logistics data and customer service metrics for the SP region.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The increase in revenue is primarily driven by the SP customer state, which contributed significantly to the change in revenue. |
| H2 | supported | The revenue increase is due to a shift in payment methods, with a significant contribution from the credit card payment type. |
| H3 | supported | The revenue increase is attributed to the seller 7d13fca15225358621be4086e1eb0964, which contributed the most to the change in revenue. |
| H4 | supported | The revenue increase is due to a category shift, with the watches_gifts category contributing the most to the change in revenue. |
| H5 | rejected | The overall increase in revenue is a result of a general market growth, not specific to any segment. |

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

**`q_ae6555`** (H3, 1 rows)

```sql
WITH m AS (
  SELECT seller_id AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-02') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-03') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-02', '2018-03')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = '7d13fca15225358621be4086e1eb0964' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| 7d13fca15225358621be4086e1eb0964 | 5935.46 | 27439.45 | 21503.99 |

**`q_060ec2`** (H4, 1 rows)

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

