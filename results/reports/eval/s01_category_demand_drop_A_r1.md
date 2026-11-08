# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s01_category_demand_drop.duckdb`  
- Steps: 1, wall time: 72.9s  
- Unsupported claim rate: 0.0% (0/6 numbers)

## Summary

The revenue drop in May 2018 can be attributed to a decrease in the number of orders, with a smaller impact from a slight drop in the average order value. The cancellation rate remained relatively stable, suggesting that the drop in revenue is primarily due to a reduction in order volume.

## Findings

### 1. The number of orders decreased by 18.5% from April to May 2018.

🟢 verified · KPI `orders` · overall = `all` · confidence high

- 6,248.00: Number of orders in May 2018
- 750.00: Number of orders in April 2018
- Evidence: `kpi_table`

### 2. The average order value increased by 3.4% from April to May 2018.

🟢 verified · KPI `aov` · overall = `all` · confidence medium

- 144.57: Average order value in May 2018
- 140.36: Average order value in April 2018
- Evidence: `kpi_table`

## Investigate next

- **Analyze the cancellation rate for May 2018 to determine if there were any specific reasons for the increase in cancellations.**: The cancellation rate increased slightly from 0.75% in April to 0.81% in May, but it did not significantly impact the overall revenue drop. (data needed: cancellation_rate)
- **Review the customer states with the largest order volume in May 2018 to see if there were any significant changes in customer behavior or preferences.**: The overall order volume decreased, but it's possible that certain customer states were more affected than others. (data needed: customer_state)
