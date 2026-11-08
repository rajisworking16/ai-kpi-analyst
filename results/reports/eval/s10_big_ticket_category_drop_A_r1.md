# KPI analysis: Why did AOV fall?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s10_big_ticket_category_drop.duckdb`  
- Steps: 1, wall time: 46.1s  
- Unsupported claim rate: 14.3% (1/7 numbers)

## Summary

The AOV fell in May 2018 compared to April 2018, likely due to a decrease in the number of orders while the revenue decreased only slightly. This suggests that the change is broad-based rather than driven by a specific segment.

## Findings

### 1. The number of orders decreased by 10.5% from 6,798 in April to 6,223 in May, while revenue decreased by only 4.3% from 973,534.09 BRL to 867,556.47 BRL.

🟡 partially verified · KPI `AOV` · overall = `all` · confidence high

- 6.22: Number of orders in May 2018
- 867,556.47: Revenue in May 2018
- 6,798.00: Number of orders in April 2018
- 973,534.09: Revenue in April 2018
- Evidence: `q_2018-04_orders`, `q_2018-05_orders`, `q_2018-04_revenue`, `q_2018-05_revenue`

## Investigate next

- **Analyze the cancellation rate for May 2018 to determine if there was an increase in cancellations that could have affected the number of orders.**: The cancellation rate in May 2018 was 0.38%, which is slightly higher than the 0.22% in April 2018, but not significantly different to explain the large drop in orders. (data needed: cancellation_rate for April and May 2018)
- **Review the customer_state distribution for May 2018 to see if there was a significant shift in the customer base that could have affected the AOV.**: The customer_state distribution did not show any significant changes, with SP and RJ still being the largest states, but the overall number of orders decreased. (data needed: customer_state distribution for April and May 2018)
