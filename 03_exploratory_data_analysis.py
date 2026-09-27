"""
03_exploratory_data_analysis.py
================================
Enterprise Exploratory Data Analysis & Machine Learning Anomaly Detection
Author: Darshan K B

Techniques Demonstrated:
- Data Ingestion from SQLite RDBMS into Pandas
- Missing Value Imputation & Data Type Casting
- Statistical Outlier Detection (IQR & Z-score)
- Unsupervised Anomaly Detection using Isolation Forest (Scikit-Learn)
- Feature Importance Modeling for Customer Churn (Random Forest)
- High-Resolution Business Visualizations (Matplotlib & Seaborn)
"""

import sqlite3
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Setup plotting style
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({'font.sans-serif': 'Segoe UI', 'font.size': 10})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VIZ_DIR = os.path.join(BASE_DIR, "visualizations")
DB_PATH = os.path.join(DATA_DIR, "enterprise_analytics.db")

os.makedirs(VIZ_DIR, exist_ok=True)

def run_eda_pipeline():
    print("=" * 60)
    print("STARTING DATA ANALYTICS & MACHINE LEARNING PIPELINE")
    print("=" * 60)

    # 1. Ingestion
    print("\n[Step 1] Ingesting tables from SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
    df_transactions = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_tickets = pd.read_sql_query("SELECT * FROM support_tickets", conn)
    conn.close()

    print(f"Loaded: Customers={df_customers.shape}, Transactions={df_transactions.shape}, Tickets={df_tickets.shape}")

    # 2. Data Cleaning & Wrangling
    print("\n[Step 2] Cleaning & Wrangling Data...")
    
    # Handle missing CSAT scores in tickets
    missing_csat = df_tickets['csat_score'].isnull().sum()
    median_csat = df_tickets['csat_score'].median()
    df_tickets['csat_score_imputed'] = df_tickets['csat_score'].fillna(median_csat)
    print(f"Imputed {missing_csat} missing CSAT values with median ({median_csat})")

    # Clean transactions: isolate negative glitch amounts
    corrupted_count = (df_transactions['amount'] < 0).sum()
    df_clean_tx = df_transactions[df_transactions['amount'] > 0].copy()
    print(f"Filtered out {corrupted_count} corrupted negative-value transactions")

    # Date parsing & temporal feature extraction
    df_clean_tx['transaction_date'] = pd.to_datetime(df_clean_tx['transaction_date'])
    df_clean_tx['year_month'] = df_clean_tx['transaction_date'].dt.to_period('M').astype(str)
    df_clean_tx['day_name'] = df_clean_tx['transaction_date'].dt.day_name()

    # 3. Statistical Outlier Detection (IQR Method)
    print("\n[Step 3] Performing Statistical Outlier Detection (IQR)...")
    q1 = df_clean_tx['amount'].quantile(0.25)
    q3 = df_clean_tx['amount'].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)
    iqr_outliers = df_clean_tx[df_clean_tx['amount'] > upper_bound]
    print(f"Amount IQR: Q1=${q1:.2f}, Q3=${q3:.2f}, IQR=${iqr:.2f}, Threshold=${upper_bound:.2f}")
    print(f"Identified {len(iqr_outliers)} statistical outliers via IQR method")

    # 4. Machine Learning Anomaly Detection (Isolation Forest)
    print("\n[Step 4] Training Isolation Forest for Threat & Spike Anomaly Detection...")
    features = ['amount', 'latency_ms']
    iso_model = IsolationForest(contamination=0.02, random_state=42)
    df_clean_tx['anomaly_pred'] = iso_model.fit_predict(df_clean_tx[features])
    # -1 represents anomaly in Isolation Forest
    df_clean_tx['is_anomaly'] = df_clean_tx['anomaly_pred'].apply(lambda x: 1 if x == -1 else 0)
    total_anomalies = df_clean_tx['is_anomaly'].sum()
    print(f"Isolation Forest identified {total_anomalies} multi-dimensional anomalies (Amount + Latency)")

    # 5. Customer 360 Feature Engineering for Churn Analysis
    print("\n[Step 5] Building Customer 360 Dataset & Feature Importance...")
    cust_tx_agg = df_clean_tx.groupby('customer_id').agg(
        total_spend=('amount', 'sum'),
        avg_spend=('amount', 'mean'),
        tx_count=('transaction_id', 'count'),
        total_anomalies=('is_anomaly', 'sum'),
        avg_latency=('latency_ms', 'mean')
    ).reset_index()

    cust_ticket_agg = df_tickets.groupby('customer_id').agg(
        ticket_count=('ticket_id', 'count'),
        avg_resolution_hrs=('resolution_hrs', 'mean'),
        avg_csat=('csat_score_imputed', 'mean')
    ).reset_index()

    c360 = df_customers.merge(cust_tx_agg, on='customer_id', how='left')
    c360 = c360.merge(cust_ticket_agg, on='customer_id', how='left')

    # Fill NaN for customers with 0 tickets
    c360['ticket_count'] = c360['ticket_count'].fillna(0)
    c360['avg_resolution_hrs'] = c360['avg_resolution_hrs'].fillna(0)
    c360['avg_csat'] = c360['avg_csat'].fillna(c360['avg_csat'].mean())
    c360['total_anomalies'] = c360['total_anomalies'].fillna(0)

    # Encode categorical features for ML
    c360_ml = pd.get_dummies(c360[['region', 'segment', 'plan_tier', 'total_spend', 'tx_count', 'avg_csat', 'ticket_count', 'avg_resolution_hrs', 'is_churned']], drop_first=True)
    
    X = c360_ml.drop('is_churned', axis=1)
    y = c360_ml['is_churned']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
    rf.fit(X_train, y_train)

    feature_importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    print("\nTop 5 Drivers of Customer Churn:")
    for feat, imp in feature_importances.head(5).items():
        print(f"  - {feat}: {imp*100:.1f}% importance")

    # 6. Generating Visualizations
    print("\n[Step 6] Generating High-Resolution Charts for Portfolio...")

    # Chart 1: Monthly Net Revenue Trend
    monthly_rev = df_clean_tx[df_clean_tx['status'] == 'Completed'].groupby('year_month')['amount'].sum().reset_index()
    plt.figure(figsize=(10, 4.5))
    plt.plot(monthly_rev['year_month'], monthly_rev['amount'], marker='o', linewidth=2.5, color='#14233c')
    plt.title('Monthly Net Revenue Velocity ($)', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Billing Month', fontweight='bold')
    plt.ylabel('Net Revenue ($)', fontweight='bold')
    plt.xticks(rotation=45)
    plt.tight_layout()
    chart1_path = os.path.join(VIZ_DIR, "monthly_revenue_trend.png")
    plt.savefig(chart1_path, dpi=200)
    plt.close()
    print(f"  Saved: {chart1_path}")

    # Chart 2: Churn Rate by Plan Tier
    churn_tier = df_customers.groupby('plan_tier')['is_churned'].mean().reset_index()
    churn_tier['churn_pct'] = churn_tier['is_churned'] * 100
    plt.figure(figsize=(7, 4.5))
    bar_plot = sns.barplot(data=churn_tier, x='plan_tier', y='churn_pct', hue='plan_tier', palette=['#c0392b', '#2980b9', '#27ae60'], legend=False)
    plt.title('Customer Churn Rate by Plan Tier (%)', fontsize=12, fontweight='bold', pad=12)
    plt.ylabel('Churn Rate (%)', fontweight='bold')
    plt.xlabel('Subscription Tier', fontweight='bold')
    for p in bar_plot.patches:
        bar_plot.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                          ha='center', va='center', color='white', fontweight='bold', fontsize=11)
    plt.tight_layout()
    chart2_path = os.path.join(VIZ_DIR, "churn_rate_by_segment_and_plan.png")
    plt.savefig(chart2_path, dpi=200)
    plt.close()
    print(f"  Saved: {chart2_path}")

    # Chart 3: Anomaly Detection Scatter Plot (Isolation Forest)
    plt.figure(figsize=(9, 5))
    sns.scatterplot(
        data=df_clean_tx, 
        x='latency_ms', 
        y='amount', 
        hue='is_anomaly', 
        palette={0: '#2b5c8f', 1: '#e74c3c'},
        alpha=0.7,
        s=35
    )
    plt.title('Transaction Anomaly Detection (Isolation Forest Multi-Feature)', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Network Latency (ms)', fontweight='bold')
    plt.ylabel('Transaction Amount ($)', fontweight='bold')
    plt.legend(title='Category', labels=['Normal Traffic', 'Anomaly / Threat Spike'])
    plt.tight_layout()
    chart3_path = os.path.join(VIZ_DIR, "transaction_anomaly_scatter.png")
    plt.savefig(chart3_path, dpi=200)
    plt.close()
    print(f"  Saved: {chart3_path}")

    # Chart 4: Support Resolution vs CSAT Score
    plt.figure(figsize=(8, 4.5))
    sns.boxplot(data=df_tickets.dropna(subset=['csat_score']), x='csat_score', y='resolution_hrs', hue='csat_score', palette='Blues_r', legend=False)
    plt.title('Impact of Ticket Resolution Time on CSAT Rating', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Customer Satisfaction Score (1 - 5)', fontweight='bold')
    plt.ylabel('Resolution Duration (Hours)', fontweight='bold')
    plt.tight_layout()
    chart4_path = os.path.join(VIZ_DIR, "csat_resolution_correlation.png")
    plt.savefig(chart4_path, dpi=200)
    plt.close()
    print(f"  Saved: {chart4_path}")

    print("\n" + "=" * 60)
    print("SUCCESS: EDA & MACHINE LEARNING PIPELINE COMPLETED")
    print(f"All 4 charts successfully generated in: {VIZ_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    run_eda_pipeline()
