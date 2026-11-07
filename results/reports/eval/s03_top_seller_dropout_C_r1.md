# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s03_top_seller_dropout.duckdb`  
- Steps: 12, wall time: 171.2s  
- Unsupported claim rate: 0.0% (0/5 numbers)

## Summary

The revenue drop in 2018-05 compared to 2018-04 is primarily due to a general decrease in the number of orders, followed by a shift in payment methods, specifically a decrease in credit card usage. The increase in the average order value for the housewares category did not significantly contribute to the revenue drop.

## Findings

### 1. A general decrease in the number of orders (254 fewer orders) is the main root cause of the revenue drop.

🟢 verified · KPI `revenue` · overall = `all` · confidence high

- -254.00: decrease in orders
- -27,728.21: total revenue change
- Evidence: `q_013299`, `decomp_revenue_category`, `decomp_revenue_customer_state`, `decomp_revenue_seller_id`, `decomp_revenue_payment_type`

### 2. A shift in payment methods, specifically a decrease in credit card usage, contributed to the revenue drop.

🟢 verified · KPI `revenue` · payment_type = `credit_card` · confidence high

- -26,050.67: revenue change from credit card
- -27,728.21: total revenue change
- Evidence: `q_40bb17`, `decomp_revenue_category`, `decomp_revenue_customer_state`, `decomp_revenue_seller_id`, `decomp_revenue_payment_type`

## Investigate next

- **Explore the reasons behind the decrease in orders from specific sellers (e.g., 7d13fca15225358621be4086e1eb0964).**: Identify if there are specific issues with these sellers that could be addressed. (data needed: Seller performance metrics, customer feedback, and seller communication logs.)
- **Analyze the payment methods used by customers in SP (customer_state) to understand the shift in payment preferences.**: Determine if there are broader trends in payment methods that could impact revenue. (data needed: Payment method usage by customer_state, customer feedback, and payment method popularity trends.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | rejected | The revenue drop in SP (customer_state) is due to a significant decrease in the housewares category. |
| H2 | supported | The revenue drop is due to a shift in payment methods, specifically a decrease in credit card usage. |
| H3 | supported | The revenue drop is due to a decrease in orders from a specific seller. |
| H4 | supported | The revenue drop is due to a general decrease in the number of orders. |
| H5 | rejected | The revenue drop is due to a change in the average order value (AOV) for the housewares category. |

## Evidence queries

**`q_013299`** (H4, 2 rows)

```sql
WITH order_counts AS (  SELECT order_month,  COUNT(DISTINCT order_id) AS orders  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY order_month) SELECT order_month, orders, orders - LAG(orders) OVER (ORDER BY order_month) AS change_in_orders FROM order_counts ORDER BY order_month DESC LIMIT 10;
```

| order_month | orders | change_in_orders |
|---|---|---|
| 2018-05 | 6544 | -254 |
| 2018-04 | 6798 |  |

**`q_2a602a`** (H1, 2 rows)

```sql
WITH revenue AS (  SELECT order_month,  SUM(CASE WHEN customer_state = 'SP' THEN price ELSE 0 END) AS revenue_sp  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY order_month) SELECT order_month, revenue_sp, revenue_sp - LAG(revenue_sp) OVER (ORDER BY order_month) AS change_in_revenue_sp FROM revenue ORDER BY order_month DESC LIMIT 10;
```

| order_month | revenue_sp | change_in_revenue_sp |
|---|---|---|
| 2018-05 | 412336.51 | 21089.52 |
| 2018-04 | 391246.99 |  |

**`q_40bb17`** (H2, 2 rows)

```sql
WITH payment_revenue AS (  SELECT order_month,  SUM(CASE WHEN payment_type = 'credit_card' THEN price ELSE 0 END) AS credit_card_revenue  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY order_month) SELECT order_month, credit_card_revenue, credit_card_revenue - LAG(credit_card_revenue) OVER (ORDER BY order_month) AS change_in_credit_card_revenue FROM payment_revenue ORDER BY order_month DESC LIMIT 10;
```

| order_month | credit_card_revenue | change_in_credit_card_revenue |
|---|---|---|
| 2018-05 | 760036.24 | -26050.67 |
| 2018-04 | 786086.91 |  |

**`q_295daf`** (H3, 10 rows)

```sql
WITH seller_revenue AS (  SELECT seller_id,  SUM(price) FILTER (WHERE order_month = '2018-04') AS prev_revenue,  SUM(price) FILTER (WHERE order_month = '2018-05') AS curr_revenue  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY seller_id) SELECT seller_id, prev_revenue, curr_revenue, curr_revenue - prev_revenue AS change_in_revenue FROM seller_revenue WHERE curr_revenue - prev_revenue < 0 ORDER BY abs(change_in_revenue) DESC LIMIT 10;
```

| seller_id | prev_revenue | curr_revenue | change_in_revenue |
|---|---|---|---|
| 5dceca129747e92ff8ef7a997dc4f8ca | 15793.92 | 6159.70 | -9634.22 |
| 4869f7a5dfa277a7dca6462dcf3b52b2 | 20386.50 | 14027.60 | -6358.90 |
| a1043bafd471dff536d0c462352beb48 | 9915.00 | 4891.00 | -5024.00 |
| e882b2a25a10b9c057cc49695f222c19 | 16097.99 | 11182.60 | -4915.39 |
| ceaec5548eefc6e23e6607c5435102e7 | 11540.64 | 6886.69 | -4653.95 |
| 0b90b6df587eb83608a64ea8b390cf07 | 6167.79 | 1618.84 | -4548.95 |
| 900ba814c251a692506d7834c1218441 | 4139.55 | 902.36 | -3237.19 |
| c826c40d7b19f62a09e2d7c5e7295ee2 | 3499.86 | 269.54 | -3230.32 |
| e5a38146df062edaf55c38afa99e42dc | 3023.46 | 61.8 | -2961.66 |
| 77530e9772f57a62c906e1c21538ab82 | 4949.30 | 2248.00 | -2701.30 |

**`q_446a76`** (H5, 2 rows)

```sql
WITH aov AS (  SELECT order_month,  AVG(price) FILTER (WHERE category = 'housewares') AS aov_housewares  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY order_month) SELECT order_month, aov_housewares, aov_housewares - LAG(aov_housewares) OVER (ORDER BY order_month) AS change_in_aov_housewares FROM aov ORDER BY order_month DESC LIMIT 10;
```

| order_month | aov_housewares | change_in_aov_housewares |
|---|---|---|
| 2018-05 | 101.66 | 5.6334 |
| 2018-04 | 96.0244 |  |

