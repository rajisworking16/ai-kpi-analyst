# KPI analysis: What changed in payments?

- Month: 2018-05  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s08_payment_mix_shift.duckdb`  
- Steps: 9, wall time: 172.0s  
- Unsupported claim rate: 0.0% (0/6 numbers)

## Summary

The main root cause of the overall decrease in orders is the significant increase in the use of vouchers as a payment type, which explains 64.07% of the volume effect in revenue. Additionally, the state of SP (customer_state) had the most disproportionate contribution to the change in late delivery rate, explaining 3.22% of the change in late delivery rate.

## Findings

### 1. The significant increase in the use of vouchers as a payment type is the main reason for the increase in revenue, explaining 64.07% of the volume effect in revenue.

🟡 partially verified · KPI `revenue` · payment_type = `voucher` · confidence high

- 64.07: excess_share
- Evidence: `q_4fdb99`, `decomp_orders_payment_type`, `revenue_split`, `decomp_revenue_category`, `decomp_orders_category`

### 2. The state of SP (customer_state) had the most disproportionate contribution to the change in late delivery rate, explaining 3.22% of the change in late delivery rate.

🟡 partially verified · KPI `late_rate` · customer_state = `SP` · confidence high

- -3.22: excess_share
- Evidence: `q_94dbc2`, `decomp_orders_customer_state`, `decomp_late_delivery_rate`

## Investigate next

- **Investigate the specific vouchers that contributed the most to the increase in revenue to understand the underlying factors driving this change.**: This will help identify if certain types of vouchers or voucher campaigns are driving the increase in revenue. (data needed: Details of voucher usage and associated orders.)
- **Analyze the delivery processes and logistics for the state of SP to understand why there was a higher proportion of late deliveries.**: This will help identify potential issues in the delivery system that could be addressed to improve delivery times. (data needed: Delivery logs, logistics data, and customer feedback.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | rejected | The significant decrease in the number of orders from customers in the state of SP (customer_state) is the primary driver of the overall decrease in orders. This is supported by the fact that SP had the most disproportionate contribution to the change in orders. |
| H2 | supported | The significant increase in the use of vouchers as a payment type is the main reason for the increase in revenue. This is supported by the fact that vouchers contributed the most to the volume effect in the revenue change split. |
| H3 | supported | The increase in the late delivery rate is due to a higher proportion of orders from the state of SP being delivered late. This is supported by the fact that SP had the most disproportionate contribution to the change in late delivery rate. |
| H4 | inconclusive | The overall decrease in orders is due to a general decline in customer activity, not specific to any segment. This is an alternative explanation to the hypotheses about specific segments. |

## Evidence queries

**`q_79a056`** (H1, 1 rows)

```sql
WITH order_changes AS (  SELECT customer_state,  SUM(CASE WHEN order_month = '2018-04' THEN 1 ELSE 0 END) AS prev_orders,  SUM(CASE WHEN order_month = '2018-05' THEN 1 ELSE 0 END) AS curr_orders  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY 1)SELECT customer_state, prev_orders, curr_orders, curr_orders - prev_orders AS change FROM order_changes WHERE customer_state = 'SP' ORDER BY abs(change) DESC LIMIT 10;
```

| customer_state | prev_orders | curr_orders | change |
|---|---|---|---|
| SP | 3488 | 3622 | 134 |

**`q_4fdb99`** (H2, 1 rows)

```sql
WITH revenue_changes AS (  SELECT payment_type,  SUM(CASE WHEN order_month = '2018-04' THEN price ELSE 0 END) AS prev_revenue,  SUM(CASE WHEN order_month = '2018-05' THEN price ELSE 0 END) AS curr_revenue  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY 1)SELECT payment_type, prev_revenue, curr_revenue, curr_revenue - prev_revenue AS change FROM revenue_changes WHERE payment_type = 'voucher' ORDER BY abs(change) DESC LIMIT 10;
```

| payment_type | prev_revenue | curr_revenue | change |
|---|---|---|---|
| voucher | 18233.59 | 482485.51 | 464251.92 |

**`q_94dbc2`** (H3, 1 rows)

```sql
WITH late_delivery AS (  SELECT customer_state,  SUM(CASE WHEN order_month = '2018-04' THEN is_late ELSE 0 END) AS prev_late,  SUM(CASE WHEN order_month = '2018-05' THEN is_late ELSE 0 END) AS curr_late  FROM orders_enriched  WHERE order_status = 'delivered' AND order_month IN ('2018-04', '2018-05')  GROUP BY 1)SELECT customer_state, prev_late, curr_late, curr_late - prev_late AS change FROM late_delivery WHERE customer_state = 'SP' ORDER BY abs(change) DESC LIMIT 10;
```

| customer_state | prev_late | curr_late | change |
|---|---|---|---|
| SP | 55 | 153 | 98 |

