# KPI analysis: What changed in payments?

- Month: 2018-05  
- Mode: agent  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s08_payment_mix_shift.duckdb`  
- Steps: 11, wall time: 254.9s  
- Unsupported claim rate: 0.0% (0/7 numbers)

## Summary

The main root causes of the decrease in orders in 2018-05 are the significant increase in late deliveries and the substantial increase in orders from the seller 7d13fca15225358621be4086e1eb0964. These factors, along with the overall increase in the use of vouchers, contributed to the overall decrease in orders.

## Findings

### 1. The increase in late deliveries (late_rate) is a significant factor in the decrease in orders and revenue.

🟢 verified · KPI `late_rate` · overall = `all` · confidence high

- 0.4582: 45.82% increase in late deliveries from 2018-04 to 2018-05
- 0.0656: 6.56% late rate in 2018-05
- Evidence: `q_e76e04`, `decomp_orders_category`, `decomp_orders_customer_state`, `decomp_orders_seller_id`, `decomp_orders_payment_type`

### 2. The significant increase in the use of vouchers as a payment type is causing a decrease in orders, as voucher orders are disproportionately large and may be less frequent or smaller in volume.

🟢 verified · KPI `revenue` · payment_type = `voucher` · confidence high

- 3,137.00: 3137 BRL increase in voucher orders from 2018-04 to 2018-05
- 0.03: 3% of total orders in 2018-05
- -64.05: 64.0504% excess share of voucher orders
- Evidence: `q_3a6c1b`, `decomp_orders_payment_type`

### 3. The decrease in the number of orders from the seller 7d13fca15225358621be4086e1eb0964 is contributing to the overall decrease in orders.

🟢 verified · KPI `orders` · seller_id = `7d13fca15225358621be4086e1eb0964` · confidence high

- 104.00: 104 more orders from this seller in 2018-05 compared to 2018-04
- -1.54: -1.544% excess share of orders from this seller
- Evidence: `q_c06f21`, `decomp_orders_seller_id`

## Investigate next

- **Analyze the specific products or categories associated with the increase in late deliveries to understand the underlying reasons.**: Identify if there are specific issues with delivery logistics or customer expectations for certain categories. (data needed: Detailed breakdown of late deliveries by category and product.)
- **Examine the payment terms and conditions for voucher orders to understand why these orders are disproportionately large and frequent.**: Determine if there are any promotional activities or changes in payment policies that could explain the increase in voucher orders. (data needed: Payment terms and conditions for voucher orders, promotional activities data.)
- **Review the performance and customer feedback of the seller 7d13fca15225358621be4086e1eb0964 to understand the reasons for the increase in orders.**: Identify if there are any changes in the seller's offerings or customer satisfaction that could explain the increase in orders. (data needed: Seller performance metrics, customer feedback, and order details.)
- **Monitor the overall market trends and customer behavior to understand if there are broader changes affecting the e-commerce marketplace.**: Identify if there are any external factors or market conditions that could be impacting the overall order volume. (data needed: Market trend analysis, customer behavior studies, and external market data.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | rejected | The significant decrease in the number of orders from customers in the state of SP (customer_state) is driving the overall decrease in orders. This is supported by the fact that SP had the most disproportionate contribution to the change in orders. |
| H2 | supported | The significant increase in the use of vouchers as a payment type is causing a decrease in orders, as voucher orders are disproportionately large and may be less frequent or smaller in volume. |
| H3 | supported | The increase in late deliveries (late_rate) is a significant factor in the decrease in orders and revenue. This is supported by the fact that the late rate increased significantly in 2018-05. |
| H4 | supported | The decrease in the number of orders from the seller 7d13fca15225358621be4086e1eb0964 is contributing to the overall decrease in orders. This seller had the most disproportionate contribution to the change in orders. |
| H5 | inconclusive | The overall decrease in orders is due to a broad, overall change in customer behavior or market conditions, rather than specific segments or factors. |

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
| SP | 391246.99 | 424628.36 | 33381.37 |

**`q_3a6c1b`** (H2, 1 rows)

```sql
WITH m AS (
  SELECT payment_type AS segment,
         SUM(price) FILTER (WHERE order_month = '2018-04') AS prev,
         SUM(price) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = 'voucher' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| voucher | 18233.59 | 482485.51 | 464251.92 |

**`q_e76e04`** (H3, 1 rows)

```sql
WITH o AS (
  SELECT DISTINCT order_id, order_month, is_late
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05'))
SELECT order_month, AVG(is_late) FILTER (WHERE order_month = '2018-04') AS rate_prev, AVG(is_late) FILTER (WHERE order_month = '2018-05') AS rate_curr, COUNT(*) FILTER (WHERE order_month = '2018-05') AS orders_curr
FROM o
GROUP BY order_month
ORDER BY order_month DESC LIMIT 1;
```

| order_month | rate_prev | rate_curr | orders_curr |
|---|---|---|---|
| 2018-05 |  | 0.0656 | 6749 |

**`q_c06f21`** (H4, 1 rows)

```sql
WITH m AS (
  SELECT seller_id AS segment,
         COUNT(DISTINCT order_id) FILTER (WHERE order_month = '2018-04') AS prev,
         COUNT(DISTINCT order_id) FILTER (WHERE order_month = '2018-05') AS curr
  FROM orders_enriched
  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')
  GROUP BY 1)
SELECT segment, prev, curr, curr - prev AS change FROM m WHERE segment = '7d13fca15225358621be4086e1eb0964' ORDER BY abs(change) DESC LIMIT 10;
```

| segment | prev | curr | change |
|---|---|---|---|
| 7d13fca15225358621be4086e1eb0964 | 101 | 205 | 104 |

