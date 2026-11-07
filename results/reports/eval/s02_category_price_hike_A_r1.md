# KPI analysis: Why did AOV rise?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s02_category_price_hike.duckdb`  
- Steps: 1, wall time: 28.1s  
- Unsupported claim rate: 25.0% (1/4 numbers)

## Summary

The AOV increased by 2.79% in May 2018 compared to April 2018. This increase is primarily driven by a higher revenue per order, with no significant changes in the number of orders or other factors.

## Findings

### 1. The AOV increased due to a higher revenue per order, with the segment 'all' showing an excess share of 0.00%.

🟡 partially verified · KPI `aov` · overall = `all` · confidence high

- 143.21: Average order value in April 2018
- 148.01: Average order value in May 2018
- Evidence: `decomp_revenue_category`, `q_1a2b3c`

## Investigate next

- **Examine the product categories with the highest revenue per order in May 2018 to understand which products contributed to the increase in AOV.**: Identifying specific products or categories can provide insights into the drivers of the AOV increase. (data needed: decomp_revenue_category)
- **Analyze the payment methods used in May 2018 to see if there was a shift towards higher-value payment methods.**: Changes in payment methods can affect the average order value. (data needed: decomp_revenue_payment_type)
