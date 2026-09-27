"""
01_data_generator.py
====================
Enterprise Analytics Data Synthesizer
Generates a realistic multi-table relational SQLite database & CSV files for:
- customers
- transactions
- support_tickets

Features:
- Realistic distributions across segments, plans, and regions
- Controlled transaction anomalies (price spikes, latency degradation, negative glitch values)
- Customer churn markers linked to lower CSAT scores and plan tiers
- Automatic export to CSV for Power BI / Tableau / Excel ingestion
"""

import sqlite3
import random
import datetime
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "enterprise_analytics.db")

def generate_enterprise_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("[1/4] Creating relational database schema...")
    cursor.execute("""
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        signup_date DATE NOT NULL,
        region TEXT NOT NULL,
        segment TEXT NOT NULL,
        plan_tier TEXT NOT NULL,
        is_churned INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE transactions (
        transaction_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        transaction_date DATE NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL,
        latency_ms INTEGER NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE support_tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        created_date DATE NOT NULL,
        category TEXT NOT NULL,
        resolution_hrs REAL NOT NULL,
        csat_score INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # Seed Customers (Pan-India Geographic Distribution)
    print("[2/4] Generating customer records across Indian regions...")
    random.seed(42)
    regions = ["South India", "West India", "North India", "East India"]
    segments = ["Enterprise", "Mid-Market", "SMB", "Consumer"]
    plans = ["Basic", "Professional", "Enterprise"]
    start_date = datetime.date(2025, 1, 1)

    customers = []
    customer_ids = []

    for i in range(1, 1001):
        cid = f"CUST-{i:04d}"
        customer_ids.append(cid)
        signup_offset = random.randint(0, 365)
        signup_dt = start_date + datetime.timedelta(days=signup_offset)
        reg = random.choices(regions, weights=[0.40, 0.30, 0.20, 0.10])[0]
        seg = random.choices(segments, weights=[0.15, 0.25, 0.40, 0.20])[0]
        plan = random.choices(plans, weights=[0.45, 0.35, 0.20])[0]
        # Churn rate higher for Basic plan
        churn = 1 if (plan == "Basic" and random.random() < 0.28) or random.random() < 0.11 else 0
        customers.append((cid, signup_dt.isoformat(), reg, seg, plan, churn))

    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?);", customers)

    # Seed Transactions (INR and Indian Payment Methods)
    print("[3/4] Generating transactions with realistic anomaly patterns...")
    payment_methods = ["UPI", "Net Banking", "Credit Card", "Corporate NEFT/RTGS"]
    transactions = []
    tx_counter = 1

    for cid in customer_ids:
        num_tx = random.randint(3, 16)
        for _ in range(num_tx):
            tid = f"TX-{tx_counter:06d}"
            tx_counter += 1
            tx_offset = random.randint(0, 420)
            tx_dt = start_date + datetime.timedelta(days=tx_offset)
            base_amount = random.uniform(30.0, 500.0)
            
            # Anomaly injection:
            # Type A: Price spike anomaly (fraud/large batch) + high network latency
            # Type B: Negative glitch values
            rand_val = random.random()
            if rand_val < 0.015:
                amount = round(base_amount * random.uniform(8.0, 14.0), 2)
                latency = random.randint(1500, 4200)
                status = random.choice(["Failed", "Refunded"])
            elif rand_val < 0.020:
                amount = round(-1.0 * base_amount, 2)
                latency = random.randint(180, 400)
                status = "Failed"
            else:
                amount = round(base_amount, 2)
                latency = random.randint(75, 420)
                status = random.choices(["Completed", "Failed", "Refunded"], weights=[0.92, 0.05, 0.03])[0]

            pay_method = random.choice(payment_methods)
            transactions.append((tid, cid, tx_dt.isoformat(), amount, pay_method, status, latency))

    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?);", transactions)

    # Seed Support Tickets
    print("[4/4] Generating support tickets and CSAT ratings...")
    categories = ["Billing Inquiry", "Technical Outage", "Feature Request", "Account Access", "Cancellation"]
    tickets = []
    ticket_counter = 1

    for cid in customer_ids:
        if random.random() < 0.48:
            num_tix = random.randint(1, 4)
            for _ in range(num_tix):
                tkid = f"TKT-{ticket_counter:05d}"
                ticket_counter += 1
                tk_offset = random.randint(20, 410)
                tk_dt = start_date + datetime.timedelta(days=tk_offset)
                cat = random.choice(categories)
                res_hrs = round(random.uniform(0.5, 52.0), 1)
                
                # CSAT is lower for long resolution times or cancellation tickets
                if res_hrs > 24.0 or cat == "Cancellation":
                    csat = random.choices([1, 2, 3], weights=[0.55, 0.30, 0.15])[0]
                else:
                    csat = random.choices([3, 4, 5], weights=[0.15, 0.45, 0.40])[0]

                # Some tickets miss CSAT score (to demonstrate missing value handling in Pandas)
                if random.random() < 0.08:
                    csat = None

                tickets.append((tkid, cid, tk_dt.isoformat(), cat, res_hrs, csat))

    cursor.executemany("INSERT INTO support_tickets VALUES (?, ?, ?, ?, ?, ?);", tickets)
    conn.commit()

    # Export to CSV for Power BI / Tableau / Excel
    print("Exporting tables to CSV files for Power BI / Tableau / Excel...")
    df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
    df_transactions = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_tickets = pd.read_sql_query("SELECT * FROM support_tickets", conn)

    df_customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
    df_transactions.to_csv(os.path.join(DATA_DIR, "transactions.csv"), index=False)
    df_tickets.to_csv(os.path.join(DATA_DIR, "support_tickets.csv"), index=False)

    conn.close()
    print("SUCCESS: Database and CSVs ready in 'data/' folder!")
    print(f"- Database: {DB_PATH}")
    print(f"- Total Customers: {len(df_customers)}")
    print(f"- Total Transactions: {len(df_transactions)}")
    print(f"- Total Support Tickets: {len(df_tickets)}")

if __name__ == "__main__":
    generate_enterprise_data()
