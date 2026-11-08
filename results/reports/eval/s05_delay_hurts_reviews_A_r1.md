# KPI analysis: Why did review scores fall?

- Month: 2018-05  
- Mode: baseline  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s05_delay_hurts_reviews.duckdb`  
- Steps: 1, wall time: 33.5s  
- Unsupported claim rate: 33.3% (1/3 numbers)

## Summary

The decrease in average review scores in May 2018 can be attributed primarily to a significant drop in the overall average review score, which was the largest change compared to the previous month. This change was broad-based, affecting all segments to a similar extent.

## Findings

### 1. The overall average review score decreased from 4.1625 in April 2018 to 4.0652 in May 2018, a drop of 2.4%.

🟡 partially verified · KPI `avg_review_score` · overall = `all` · confidence high

- 4.16: Average review score in April 2018
- 4.07: Average review score in May 2018
- Evidence: `kpi_table`

## Investigate next

- **Analyze the distribution of review scores across different categories to identify any specific categories that may have contributed more significantly to the overall decrease.**: Some categories might have seen a more pronounced drop in review scores, which could provide insights into the root cause of the overall decrease. (data needed: decomp_review_score_category)
- **Examine the reasons behind the increase in late delivery rate from 4.5% in April to 9.8% in May.**: Late deliveries can negatively impact customer satisfaction and review scores, and understanding the reasons behind this increase could help explain the drop in review scores. (data needed: decomp_late_delivery_reasons)
