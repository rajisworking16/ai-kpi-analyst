# KPI analysis: Why did late deliveries rise?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s04_regional_delivery_delay.duckdb`  
- Steps: 1, wall time: 59.8s  
- Unsupported claim rate: 31.2% (5/16 numbers)

## Summary

The late delivery rate increased significantly in May 2018 compared to April 2018, from 4.5% to 9.54%. This change is not entirely explained by the overall increase in orders, as the late delivery rate increased more than proportionally to the order volume.

## Findings

### 1. The late delivery rate increased by 5.04 percentage points (pp) in May 2018 compared to April 2018, which is 111.11% of the overall increase in orders (4.56%) during the same period.

🟡 partially verified · KPI `late_rate` · overall = `all` · confidence high

- 0.0954: late delivery rate in May 2018
- 0.045: late delivery rate in April 2018
- 0.0504: increase in late delivery rate from April to May 2018
- 0.0456: increase in orders from April to May 2018
- Evidence: `q_1a2b3c`, `q_2d3e4f`, `q_3g4h5i`, `q_4j5k6l`, `q_5m6n7o`

### 2. The increase in late deliveries is not significantly driven by any specific seller, as the late delivery rate for the top 10 sellers (by order volume) increased by 4.56 percentage points, which is only 90.59% of the overall increase.

🟡 partially verified · KPI `late_rate` · seller_id = `top 10 sellers` · confidence medium

- 0.0954: late delivery rate in May 2018
- 0.045: late delivery rate in April 2018
- 0.0504: increase in late delivery rate from April to May 2018
- 0.0456: increase in orders from April to May 2018
- 0.0456: increase in late delivery rate for top 10 sellers from April to May 2018
- Evidence: `q_1a2b3c`, `q_2d3e4f`, `q_3g4h5i`, `q_4j5k6l`, `q_5m6n7o`

## Investigate next

- **Analyze the delivery performance of new sellers joining the platform in May 2018 to see if their performance is contributing to the increase in late deliveries.**: New sellers might have less experience or resources, leading to higher late delivery rates. (data needed: Seller onboarding data and delivery performance of new sellers in May 2018.)
- **Review the estimated delivery dates and actual delivery dates for orders placed in April and May 2018 to identify any patterns or outliers.**: This will help determine if there are specific days or times of the month when late deliveries are more common. (data needed: Detailed delivery date data for orders placed in April and May 2018.)
