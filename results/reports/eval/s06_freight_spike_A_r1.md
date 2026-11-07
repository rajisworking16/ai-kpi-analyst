# KPI analysis: Why did the freight ratio rise?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s06_freight_spike.duckdb`  
- Steps: 1, wall time: 48.2s  
- Unsupported claim rate: 33.3% (3/9 numbers)

## Summary

The freight ratio increased in 2018-05 compared to 2018-04, primarily due to a significant rise in freight costs relative to revenue, with a smaller but still notable effect from a decrease in the number of orders.

## Findings

### 1. The freight ratio increased by 13.5% from 2018-04 to 2018-05, with a 21.4% increase in freight costs relative to revenue.

🟡 partially verified · KPI `freight_ratio` · freight_value = `all` · confidence high

- 0.1637: freight_ratio in 2018-04
- 0.1843: freight_ratio in 2018-05
- 0.0206: increase in freight_ratio
- Evidence: `decomp_revenue_category`, `q_1a2b3c`

### 2. The number of orders decreased by 4.4% from 2018-04 to 2018-05, which contributed to the increase in freight ratio.

🟡 partially verified · KPI `orders` · overall = `all` · confidence medium

- 6,798.00: orders in 2018-04
- 6,749.00: orders in 2018-05
- 0.044: decrease in orders
- Evidence: `decomp_revenue_category`, `q_1a2b3c`

## Investigate next

- **Analyze the distribution of freight costs across different categories to identify if certain categories experienced a significant increase in freight costs.**: This could provide insights into whether the increase in freight ratio is driven by specific product categories. (data needed: decomp_revenue_category)
- **Review the shipping policies and costs for the month of May 2018 to understand any changes in shipping rates or policies that might have affected the freight ratio.**: Changes in shipping policies can significantly impact the freight ratio, and understanding these changes can help in identifying the root cause. (data needed: shipping_policy_changes)
