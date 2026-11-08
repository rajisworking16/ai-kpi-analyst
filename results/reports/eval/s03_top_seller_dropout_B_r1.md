# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: agent  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s03_top_seller_dropout.duckdb`  
- Steps: 12, wall time: 194.1s  
- Unsupported claim rate: 16.7% (1/6 numbers)

## Summary

The revenue drop in 2018-05 compared to 2018-04 is primarily due to a general decrease in the number of orders, followed by a significant decrease in the number of orders from a specific seller, and a change in the average order value for the home_appliances category. These factors collectively explain the majority of the revenue decline.

## Findings

### 1. A general decrease in the number of orders (254 fewer orders in 2018-05 compared to 2018-04) is the main root cause of the revenue drop.

🟢 verified · KPI `revenue` · overall = `all` · confidence high

- -254.00: decrease in orders
- Evidence: `q_013299`, `decomp_revenue_category`, `decomp_revenue_customer_state`, `decomp_revenue_seller_id`, `decomp_revenue_payment_type`

### 2. A significant decrease in the number of orders from the seller 5dceca129747e92ff8ef7a997dc4f8ca (-9634.22 BRL) is a major contributor to the revenue drop.

🟢 verified · KPI `revenue` · seller_id = `5dceca129747e92ff8ef7a997dc4f8ca` · confidence high

- -9,634.22: revenue change
- Evidence: `q_295daf`, `decomp_revenue_seller_id`

### 3. A decrease in the average order value (AOV) for the home_appliances category (from 144.42 to 96.0886 BRL) contributed to the revenue drop.

🟡 partially verified · KPI `revenue` · category = `home_appliances` · confidence high

- -48.33: change in AOV
- Evidence: `q_3f99b4`, `decomp_revenue_category`

## Investigate next

- **Analyze the specific reasons for the decrease in orders from seller 5dceca129747e92ff8ef7a997dc4f8ca to understand if there are any underlying issues that need to be addressed.**: This seller had a significant impact on the revenue drop, and understanding the root cause can help in mitigating future losses. (data needed: Seller performance metrics, customer feedback, and order details.)
- **Explore the factors contributing to the change in the average order value for the home_appliances category.**: Identifying the reasons behind the AOV decrease can help in formulating strategies to stabilize or increase the AOV. (data needed: Product pricing trends, customer reviews, and market conditions.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | supported | The revenue drop in SP (customer_state) is due to a significant decrease in the housewares category. |
| H2 | supported | The revenue drop is due to a shift in payment methods, specifically a decrease in credit card usage. |
| H3 | supported | The revenue drop is due to a decrease in orders from a specific seller. |
| H4 | supported | The revenue drop is due to a general decrease in the number of orders. |
| H5 | supported | The revenue drop is due to a change in the average order value (AOV) for the home_appliances category. |

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

**`q_3f99b4`** (H5, 2 rows)

```sql
WITH aov AS (  SELECT order_month,  AVG(price) FILTER (WHERE category = 'home_appliances' AND order_month = '2018-04') AS aov_prev,  AVG(price) FILTER (WHERE category = 'home_appliances' AND order_month = '2018-05') AS aov_curr  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY order_month) SELECT order_month, aov_prev, aov_curr, aov_curr - aov_prev AS change_in_aov FROM aov ORDER BY order_month DESC LIMIT 10;
```

| order_month | aov_prev | aov_curr | change_in_aov |
|---|---|---|---|
| 2018-05 |  | 96.0886 |  |
| 2018-04 | 144.42 |  |  |

