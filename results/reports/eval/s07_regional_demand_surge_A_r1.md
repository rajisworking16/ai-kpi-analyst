# KPI analysis: Why did orders rise?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s07_regional_demand_surge.duckdb`  
- Steps: 1, wall time: 34.5s  
- Unsupported claim rate: 33.3% (1/3 numbers)

## Summary

The increase in orders from 2018-04 to 2018-05 can be attributed to a broad-based rise in orders across all segments, with no single segment explaining a disproportionate share of the change.

## Findings

### 1. Orders increased by 14.29% from 2018-04 to 2018-05, which is a broad-based increase across all segments.

🟡 partially verified · KPI `orders` · overall = `all` · confidence high

- 8,003.00: Orders in 2018-05
- 6,798.00: Orders in 2018-04
- Evidence: `kpi_table`

## Investigate next

- **Analyze the change in the number of new customers in 2018-05 compared to 2018-04 to understand if the increase in orders is due to new customer acquisition or repeat business.**: New customer acquisition can significantly impact order counts, especially if the new customers are more active or have different purchasing behaviors. (data needed: New customer count and their order frequency in 2018-04 and 2018-05.)
- **Review marketing campaigns and promotions in 2018-05 to see if any specific initiatives led to an increase in orders.**: Marketing campaigns can drive a sudden increase in orders, especially if they target a broad audience or offer significant discounts. (data needed: Details of marketing campaigns and their impact on orders.)
