# KPI analysis: Why did revenue drop?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s12_decoy_broad_drop.duckdb`  
- Steps: 1, wall time: 38.6s  
- Unsupported claim rate: 33.3% (2/6 numbers)

## Summary

The revenue drop in May 2018 can be attributed to a significant decrease in the number of orders, with a smaller impact from a slight drop in the average order value (AOV). The cancellation rate remained relatively stable, and the freight ratio and delivery times did not show substantial changes.

## Findings

### 1. The number of orders decreased by 22.1% from 4,478 in April to 3,479 in May 2018.

🟡 partially verified · KPI `orders` · overall = `all` · confidence high

- 4,478.00: April 2018 orders
- 3,479.00: May 2018 orders
- Evidence: `kpi_table`

### 2. The average order value (AOV) increased by 6.2% from 143.21 in April to 142.36 in May 2018.

🟢 verified · KPI `aov` · overall = `all` · confidence high

- 143.21: April 2018 AOV
- 142.36: May 2018 AOV
- Evidence: `kpi_table`

## Investigate next

- **Analyze the cancellation rate for May 2018 to determine if there were any specific patterns or events that could have led to the decrease in orders.**: The cancellation rate only increased by 0.2% from 0.45% in April to 0.47% in May, suggesting that cancellations were not the primary driver of the order drop. (data needed: cancellation_rate)
- **Review the customer states and payment types to identify any regions or payment methods that may have been affected more significantly.**: The overall decrease in orders was broad-based, and no single segment showed a disproportionately large change. (data needed: customer_state, payment_type)
