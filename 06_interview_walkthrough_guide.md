# Interview Walkthrough Guide: Master Your Project
**Project Name:** Enterprise Customer Intelligence & Anomaly Analytics Platform  
**Target Roles:** Data Analyst, Business Intelligence Analyst, Analytics Engineer  
**Candidate:** Darshan K B  

---

## 1. The 90-Second Opening Pitch (When Asked: "Walk Me Through Your Project")

> *"In this project, I engineered an end-to-end Enterprise Analytics and Risk Intelligence platform to solve two core business problems: customer churn and transactional anomalies.*
> 
> *I designed a multi-table relational schema covering customers, payment transactions, and support tickets. Using **SQL**, I extracted key financial metrics, built rolling moving averages, and calculated month-over-month revenue growth using window functions like `LAG()` and `DENSE_RANK()`.
> 
> *In **Python**, I performed exploratory data analysis with Pandas, imputed missing customer satisfaction values, and trained an unsupervised **Isolation Forest model** that detected over 180 multi-variable anomalies—such as transaction price spikes coupled with network latency degradation.
> 
> *Finally, I integrated an **Agentic AI workflow with Claude and Gemini** to automate executive summary generation from raw data, and designed interactive KPI dashboards in **Power BI and Tableau** to visualize customer lifetime value and churn risk drivers.*
> 
> *The insights proved that customers experiencing support ticket delays over 24 hours had a 55% decline in CSAT, identifying a key precursor to churn in entry-level plans."*

---

## 2. Technical Questions the Interviewer Will Ask (And Exact Answers)

### Q1: "How did you use SQL window functions in this project?"
**Your Answer:**  
*"I used window functions in two key areas:*
1. *I used `LAG(net_revenue, 1) OVER (ORDER BY transaction_month)` within a CTE to compare the current month's revenue against the previous month, computing the exact Month-over-Month (MoM) growth percentage.*
2. *I used `DENSE_RANK() OVER (PARTITION BY region ORDER BY total_spend DESC)` to rank the top 5 spenders within each geographical region without skipping rank positions on ties.*
3. *I also computed a 30-day moving average using `ROWS BETWEEN 29 PRECEDING AND CURRENT ROW` to smooth out daily transaction volatility."*

---

### Q2: "How did you handle data cleaning and missing values in Pandas?"
**Your Answer:**  
*"During the data ingestion phase, I found that ~8% of support tickets were missing CSAT scores because customers abandoned the feedback survey. Instead of dropping these rows—which would lose critical ticket resolution data—I imputed the missing scores using the median value (2.0) after verifying that the distribution was skewed.*
*Additionally, I identified negative transaction values that represented system glitches, isolated them into an audit log, and filtered them out so they wouldn't distort topline revenue."*

---

### Q3: "Why did you use Isolation Forest instead of standard standard deviation or IQR for anomaly detection?"
**Your Answer:**  
*"IQR and Z-scores are univariate—they can only evaluate one variable at a time, such as checking if a dollar amount is unusually high. But in real-world cloud security and payment transactions, an anomaly often involves multiple subtle dimensions: for example, a moderate transaction amount that occurs with an extreme 3,500ms network latency and an unusual status.*
*Isolation Forest is an unsupervised tree-based algorithm that isolates anomalies by randomly partitioning feature space. Because anomalies require fewer splits to be isolated, it efficiently flags multi-dimensional outliers without requiring pre-labeled training data."*

---

### Q4: "How does the Generative AI / Agentic AI part actually work?"
**Your Answer:**  
*"I built an analytical copilot script that consumes aggregated JSON metrics from our SQL queries and machine learning models. Using prompt engineering, I structured an analytical role prompt that asks the LLM (Claude or Gemini API) to act as a Strategic Data Analyst. The model ingests the quantitative KPIs, identifies the delta between baseline churn and high-risk tiers, and automatically compiles a polished, C-suite executive briefing with strategic recommendations.*
*This demonstrates how modern analysts can automate repetitive weekly reporting and spend more time on deep exploratory work."*

---

### Q5: "What DAX measures did you create in Power BI?"
**Your Answer:**  
*"I created measures for Total Net Revenue using `CALCULATE` and conditional filters for completed status, Average Order Value (AOV) using `DIVIDE` to avoid division-by-zero errors, and Month-over-Month Revenue Growth using `DATEADD` to fetch the previous month's value dynamically across visual slicers."*
