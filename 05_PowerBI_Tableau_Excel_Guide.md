# Power BI, Tableau & MS Excel Implementation Guide
**Dataset Location:** `data/customers.csv`, `data/transactions.csv`, `data/support_tickets.csv`  
**Author:** Darshan K B  

---

## 1. Power BI Dashboard Blueprint

### A. Data Model Setup (Star Schema)
1. Open **Power BI Desktop**.
2. Click **Get Data** $\rightarrow$ **Text/CSV**, and import all 3 files from the `data/` folder:
   - `customers.csv` (Dimension Table)
   - `transactions.csv` (Fact Table)
   - `support_tickets.csv` (Fact Table)
3. Navigate to the **Model View** and verify relationships:
   - `customers[customer_id]` (1) $\longleftrightarrow$ `transactions[customer_id]` (*) [One-to-Many, Single Direction]
   - `customers[customer_id]` (1) $\longleftrightarrow$ `support_tickets[customer_id]` (*) [One-to-Many, Single Direction]

### B. Core DAX Measures (Copy & Paste Ready)

#### 1. Total Net Completed Revenue:
```dax
Total Net Revenue = 
CALCULATE(
    SUM(transactions[amount]),
    transactions[status] = "Completed",
    transactions[amount] > 0
)
```

#### 2. Average Order Value (AOV):
```dax
Average Order Value = 
DIVIDE(
    [Total Net Revenue],
    CALCULATE(COUNTROWS(transactions), transactions[status] = "Completed", transactions[amount] > 0),
    0
)
```

#### 3. Churn Rate %:
```dax
Churn Rate Pct = 
VAR TotalCust = COUNTROWS(customers)
VAR ChurnedCust = CALCULATE(COUNTROWS(customers), customers[is_churned] = 1)
RETURN
DIVIDE(ChurnedCust, TotalCust, 0)
```

#### 4. Month-over-Month (MoM) Revenue Growth %:
```dax
Previous Month Revenue = 
CALCULATE(
    [Total Net Revenue],
    DATEADD('transactions'[transaction_date], -1, MONTH)
)

MoM Revenue Growth Pct = 
DIVIDE(
    [Total Net Revenue] - [Previous Month Revenue],
    [Previous Month Revenue],
    0
)
```

#### 5. Anomaly Indicator Flag (DAX Calculated Column in `transactions`):
```dax
Is_Flagged_Anomaly = 
IF(
    transactions[amount] > 1000 || transactions[latency_ms] > 2500 || transactions[amount] < 0,
    "High Risk / Anomaly",
    "Normal"
)
```

### C. Recommended Visual Canvas Layout:
- **Top Row (KPI Cards):** Net Revenue, Total Customers, Churn Rate %, Average CSAT.
- **Middle Left (Line Chart):** Monthly Revenue Velocity with MoM trend.
- **Middle Right (Clustered Bar Chart):** Churn Rate % broken down by `plan_tier` and `segment`.
- **Bottom Left (Scatter Plot):** Network Latency (`latency_ms`) vs Transaction Amount (`amount`) colored by `Is_Flagged_Anomaly`.
- **Bottom Right (Matrix Table):** Top Spenders per Region with ranking.

---

## 2. Tableau Visualization Guide

### Calculated Fields in Tableau:
1. **Net Revenue:**
   ```tableau
   IF [Status] = "Completed" AND [Amount] > 0 THEN [Amount] ELSE 0 END
   ```
2. **Customer Churn Flag:**
   ```tableau
   IF [Is Churned] = 1 THEN "Churned" ELSE "Active" END
   ```
3. **CSAT Satisfaction Category:**
   ```tableau
   IF [Csat Score] >= 4 THEN "High Satisfaction (4-5)"
   ELSEIF [Csat Score] = 3 THEN "Neutral (3)"
   ELSE "Low Satisfaction (1-2)"
   END
   ```

### Dashboard Actions:
- Add a **Region Slicer** and **Plan Tier Slicer** to allow dynamic cross-filtering between tickets and revenue.

---

## 3. Advanced MS Excel Analytics Guide

### A. Dynamic Data Modeling with XLOOKUP
In `transactions.csv`, add a new column `Customer_Plan` to enrich transactions with customer tier:
```excel
=XLOOKUP(B2, customers!$A$2:$A$1001, customers!$E$2:$E$1001, "Not Found", 0)
```

### B. Dynamic Customer Total Spend (SUMIFS)
In `customers.csv`, calculate lifetime value directly:
```excel
=SUMIFS(transactions!$D:$D, transactions!$B:$B, A2, transactions!$F:$F, "Completed")
```

### C. Pivot Tables & What-If Scenario Analysis:
1. **Pivot Table 1:** Rows = `plan_tier`, Columns = `is_churned`, Values = Count of `customer_id` (Show Values As: `% of Row Total`).
2. **Pivot Table 2:** Rows = `payment_method`, Values = Sum of `amount`, Average of `latency_ms`.
