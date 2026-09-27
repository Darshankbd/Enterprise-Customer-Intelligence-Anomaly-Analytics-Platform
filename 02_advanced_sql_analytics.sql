-- ==============================================================================
-- 02_advanced_sql_analytics.sql
-- Enterprise Analytics & Business Intelligence SQL Suite
-- Author: Darshan K B
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXECUTIVE KPI OVERVIEW
-- Summary of overall business health, volume, and customer base
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT c.customer_id) AS total_customers,
    COUNT(t.transaction_id) AS total_transactions,
    ROUND(SUM(CASE WHEN t.status = 'Completed' AND t.amount > 0 THEN t.amount ELSE 0 END), 2) AS net_revenue,
    ROUND(AVG(CASE WHEN t.status = 'Completed' AND t.amount > 0 THEN t.amount END), 2) AS average_order_value,
    ROUND(100.0 * SUM(c.is_churned) / COUNT(DISTINCT c.customer_id), 2) AS overall_churn_rate_pct
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id;


-- ------------------------------------------------------------------------------
-- 2. MONTH-OVER-MONTH (MoM) REVENUE GROWTH USING WINDOW FUNCTIONS (LAG)
-- Uses CTE and LAG() to measure monthly financial velocity
-- ------------------------------------------------------------------------------
WITH MonthlyFinancials AS (
    SELECT 
        STRFTIME('%Y-%m', transaction_date) AS transaction_month,
        COUNT(transaction_id) AS monthly_transactions,
        ROUND(SUM(amount), 2) AS gross_revenue,
        ROUND(SUM(CASE WHEN status = 'Completed' AND amount > 0 THEN amount ELSE 0 END), 2) AS net_revenue
    FROM transactions
    GROUP BY STRFTIME('%Y-%m', transaction_date)
)
SELECT 
    transaction_month,
    monthly_transactions,
    net_revenue,
    LAG(net_revenue, 1) OVER (ORDER BY transaction_month) AS previous_month_revenue,
    ROUND(
        100.0 * (net_revenue - LAG(net_revenue, 1) OVER (ORDER BY transaction_month)) 
        / NULLIF(LAG(net_revenue, 1) OVER (ORDER BY transaction_month), 0), 
        2
    ) AS mom_growth_rate_pct
FROM MonthlyFinancials
ORDER BY transaction_month;


-- ------------------------------------------------------------------------------
-- 3. CUSTOMER SPEND RANKING PER REGION USING DENSE_RANK() & CTEs
-- Identifies top 5 enterprise customers in each geographical region
-- ------------------------------------------------------------------------------
WITH CustomerSpend AS (
    SELECT 
        c.customer_id,
        c.region,
        c.segment,
        c.plan_tier,
        ROUND(SUM(CASE WHEN t.status = 'Completed' AND t.amount > 0 THEN t.amount ELSE 0 END), 2) AS total_spend
    FROM customers c
    JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id, c.region, c.segment, c.plan_tier
),
RankedCustomers AS (
    SELECT 
        customer_id,
        region,
        segment,
        plan_tier,
        total_spend,
        DENSE_RANK() OVER (PARTITION BY region ORDER BY total_spend DESC) AS region_spend_rank
    FROM CustomerSpend
)
SELECT 
    region,
    region_spend_rank,
    customer_id,
    segment,
    plan_tier,
    total_spend
FROM RankedCustomers
WHERE region_spend_rank <= 5
ORDER BY region, region_spend_rank;


-- ------------------------------------------------------------------------------
-- 4. 30-DAY ROLLING AVERAGE OF DAILY TRANSACTION VOLUME
-- Demonstrates moving average window functions for smoothing time-series trends
-- ------------------------------------------------------------------------------
WITH DailyAggregates AS (
    SELECT 
        transaction_date,
        COUNT(transaction_id) AS daily_tx_count,
        ROUND(SUM(CASE WHEN status = 'Completed' AND amount > 0 THEN amount ELSE 0 END), 2) AS daily_net_revenue
    FROM transactions
    GROUP BY transaction_date
)
SELECT 
    transaction_date,
    daily_tx_count,
    daily_net_revenue,
    ROUND(
        AVG(daily_net_revenue) OVER (
            ORDER BY transaction_date 
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS rolling_30day_avg_revenue
FROM DailyAggregates
ORDER BY transaction_date;


-- ------------------------------------------------------------------------------
-- 5. CHURN CORRELATION BY PLAN TIER & CSAT SATISFACTION METRICS
-- Demonstrates multi-table JOINs, conditional aggregations, and business insight extraction
-- ------------------------------------------------------------------------------
SELECT 
    c.plan_tier,
    c.segment,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    SUM(c.is_churned) AS churned_customers,
    ROUND(100.0 * SUM(c.is_churned) / COUNT(DISTINCT c.customer_id), 2) AS churn_rate_pct,
    ROUND(AVG(t.resolution_hrs), 1) AS avg_ticket_resolution_hours,
    ROUND(AVG(t.csat_score), 2) AS avg_csat_score
FROM customers c
LEFT JOIN support_tickets t ON c.customer_id = t.customer_id
GROUP BY c.plan_tier, c.segment
ORDER BY churn_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- 6. STATISTICAL TRANSACTION ANOMALY IDENTIFICATION
-- Detects transactions exceeding 3x the customer's historical average amount
-- ------------------------------------------------------------------------------
WITH CustomerBaselines AS (
    SELECT 
        customer_id,
        AVG(amount) AS cust_avg_amount,
        COUNT(transaction_id) AS tx_history_count
    FROM transactions
    WHERE amount > 0
    GROUP BY customer_id
)
SELECT 
    t.transaction_id,
    t.customer_id,
    t.transaction_date,
    t.amount,
    ROUND(b.cust_avg_amount, 2) AS historical_avg_amount,
    ROUND(t.amount / b.cust_avg_amount, 1) AS anomaly_multiple,
    t.latency_ms,
    t.status
FROM transactions t
JOIN CustomerBaselines b ON t.customer_id = b.customer_id
WHERE t.amount > (3.0 * b.cust_avg_amount)
   OR t.latency_ms > 2500
   OR t.amount < 0
ORDER BY t.amount DESC
LIMIT 20;
