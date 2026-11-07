# KPI analysis: Why did cancellations rise?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s09_cancellation_spike.duckdb`  
- Steps: 1, wall time: 35.9s  
- Unsupported claim rate: 0.0% (0/2 numbers)

## Summary

The increase in the cancellation rate in May 2018 can be attributed to a broad-based change, as all segments experienced an increase in cancellations, albeit to varying degrees.

## Findings

### 1. The cancellation rate increased across all segments, with no single segment explaining a disproportionate share of the change.

🟡 partially verified · KPI `cancellation_rate` · overall = `all` · confidence high

- 0.0214: The cancellation rate in May 2018 was 2.14%.
- 0.0075: The cancellation rate in April 2018 was 0.75%, a 1.39 percentage point increase.
- Evidence: `q_1a2b3c`, `q_2d4e5f`, `q_3g6h7i`, `q_4j8k9l`, `q_5m0n1o`

## Investigate next

- **Review the customer feedback and support tickets from May 2018 to identify common issues that may have led to more cancellations.**: Understanding the reasons behind the cancellations can help in addressing the root cause and improving customer satisfaction. (data needed: Customer feedback and support ticket data for May 2018.)
- **Analyze the payment methods used in May 2018 to see if there is a correlation between payment type and cancellation rate.**: Some payment methods might be more prone to cancellations, which could provide insights into the issue. (data needed: Payment method data for May 2018.)
