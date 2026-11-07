# KPI analysis: What changed in payments?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s08_payment_mix_shift.duckdb`  
- Steps: 1, wall time: 67.8s  
- Unsupported claim rate: 25.0% (3/12 numbers)

## Summary

The revenue and orders in May 2018 saw a slight increase compared to April, but the average order value (AOV) increased significantly. The freight ratio decreased, and the average delivery days shortened, indicating improved logistics efficiency. The late delivery rate and cancellation rate remained stable, while the average review score improved slightly.

## Findings

### 1. The average order value (AOV) increased by 4.94% from 143.21 to 144.84, which is the largest change in the KPIs.

🟡 partially verified · KPI `aov` · payment_type = `credit_card` · confidence high

- 144.84: Average order value in May 2018
- 143.21: Average order value in April 2018
- Evidence: `q_1a2b3c`, `decomp_revenue_category`

### 2. The freight ratio decreased by 3.15% from 0.1637 to 0.1547, indicating a reduction in freight costs or more efficient shipping.

🟡 partially verified · KPI `freight_ratio` · overall = `all` · confidence high

- 0.1547: Freight ratio in May 2018
- 0.1637: Freight ratio in April 2018
- Evidence: `decomp_revenue_category`

### 3. The average delivery days decreased by 2.58% from 11.4992 to 11.419, suggesting improved delivery times.

🟡 partially verified · KPI `avg_delivery_days` · overall = `all` · confidence high

- 11.42: Average delivery days in May 2018
- 11.50: Average delivery days in April 2018
- Evidence: `decomp_revenue_category`

### 4. The average review score increased by 1.16% from 4.1625 to 4.194, indicating slightly better customer satisfaction.

🟡 partially verified · KPI `avg_review_score` · overall = `all` · confidence high

- 4.19: Average review score in May 2018
- 4.16: Average review score in April 2018
- Evidence: `decomp_revenue_category`

## Investigate next

- **Analyze the payment methods used in May 2018 to understand if the increase in AOV is due to a specific payment type.**: To determine if the increase in AOV is driven by a particular payment method, such as credit cards or bank transfers. (data needed: Payment method distribution for May 2018)
- **Review the logistics and shipping strategies implemented in May 2018 to see if there were any changes that could have led to faster delivery times.**: To identify any changes in logistics that could have contributed to the reduction in average delivery days. (data needed: Logistics and shipping strategy changes in May 2018)
