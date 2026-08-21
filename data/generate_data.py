"""
Generates a synthetic retail-enterprise dataset simulating the 8 business
systems described in the case study (ERP, CRM, HRMS, POS, Inventory, Finance,
Marketing, Support) at a scale a laptop can actually run.

Run:  python -m data.generate_data
Output: CSV files in data/csv/
"""
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "csv")
os.makedirs(OUT_DIR, exist_ok=True)

COUNTRIES = ["Pakistan", "UAE", "UK"]
CITIES = {
    "Pakistan": ["Islamabad", "Lahore", "Karachi"],
    "UAE": ["Dubai", "Abu Dhabi"],
    "UK": ["London", "Manchester"],
}
CATEGORIES = ["Electronics", "Groceries", "Apparel", "Home & Living", "Beauty"]
DEPARTMENTS = ["Sales", "Operations", "Marketing", "Finance", "HR", "IT"]
ISSUE_TYPES = ["Delivery Delay", "Product Defect", "Refund Request", "Billing Issue", "Other"]

N_STORES = 12
N_PRODUCTS = 40
N_EMPLOYEES = 60
N_VENDORS = 10
N_CAMPAIGNS = 8
N_SUPPORT_TICKETS = 400
SALES_DAYS = 180  # ~6 months of daily sales history


def gen_stores():
    rows = []
    for i in range(1, N_STORES + 1):
        country = random.choice(COUNTRIES)
        city = random.choice(CITIES[country])
        rows.append({
            "store_id": i, "name": f"Store-{city}-{i}", "city": city,
            "country": country, "size_sqft": random.randint(2000, 15000),
        })
    return pd.DataFrame(rows)


def gen_products():
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        category = random.choice(CATEGORIES)
        rows.append({
            "product_id": i, "name": f"{category}-Item-{i}", "category": category,
            "price": round(random.uniform(5, 500), 2), "cost": round(random.uniform(2, 300), 2),
        })
    return pd.DataFrame(rows)


def gen_employees(stores_df):
    rows = []
    for i in range(1, N_EMPLOYEES + 1):
        store_id = random.choice(stores_df["store_id"].tolist())
        rows.append({
            "employee_id": i, "name": f"Employee-{i}", "department": random.choice(DEPARTMENTS),
            "store_id": store_id, "salary": round(random.uniform(30000, 120000), 2),
            "hire_date": str(date(2020, 1, 1) + timedelta(days=random.randint(0, 1800))),
        })
    return pd.DataFrame(rows)


def gen_vendors():
    rows = []
    for i in range(1, N_VENDORS + 1):
        rows.append({
            "vendor_id": i, "name": f"Vendor-{i}",
            "reliability_score": round(random.uniform(0.6, 1.0), 2),
            "avg_lead_time_days": random.randint(2, 20),
        })
    return pd.DataFrame(rows)


def gen_campaigns():
    rows = []
    for i in range(1, N_CAMPAIGNS + 1):
        start = date(2025, 1, 1) + timedelta(days=random.randint(0, 150))
        rows.append({
            "campaign_id": i, "name": f"Campaign-{i}", "channel": random.choice(["Social", "Email", "TV", "Search"]),
            "budget": round(random.uniform(2000, 50000), 2),
            "start_date": str(start), "end_date": str(start + timedelta(days=random.randint(7, 45))),
        })
    return pd.DataFrame(rows)


def gen_sales(stores_df, products_df):
    rows = []
    sale_id = 1
    start_date = date.today() - timedelta(days=SALES_DAYS)

    # deliberate underperformance/decline trends so the analytics modules
    # have real patterns to surface (not just noise)
    declining_stores = set(random.sample(stores_df["store_id"].tolist(), 2))
    declining_products = set(random.sample(products_df["product_id"].tolist(), 3))

    for day_offset in range(SALES_DAYS):
        d = start_date + timedelta(days=day_offset)
        for store_id in stores_df["store_id"]:
            n_transactions = random.randint(3, 15)
            for _ in range(n_transactions):
                product = products_df.sample(1).iloc[0]
                qty = random.randint(1, 5)
                price = product["price"]

                trend_factor = 1.0
                if store_id in declining_stores:
                    trend_factor *= max(0.3, 1 - (day_offset / SALES_DAYS) * 0.6)
                if product["product_id"] in declining_products:
                    trend_factor *= max(0.4, 1 - (day_offset / SALES_DAYS) * 0.5)

                revenue = round(qty * price * trend_factor, 2)
                rows.append({
                    "sale_id": sale_id, "store_id": store_id, "product_id": product["product_id"],
                    "date": str(d), "quantity": qty, "revenue": revenue,
                })
                sale_id += 1
    return pd.DataFrame(rows)


def gen_support_tickets(stores_df):
    rows = []
    # give 2 stores an elevated ticket volume -> churn-risk alert candidates
    hot_stores = set(random.sample(stores_df["store_id"].tolist(), 2))
    for i in range(1, N_SUPPORT_TICKETS + 1):
        store_id = random.choice(
            list(hot_stores) * 4 + stores_df["store_id"].tolist()  # weight hot stores
        )
        rows.append({
            "ticket_id": i, "store_id": store_id,
            "issue_type": random.choice(ISSUE_TYPES),
            "date": str(date.today() - timedelta(days=random.randint(0, SALES_DAYS))),
            "resolved_in_hours": round(random.uniform(2, 96), 1),
        })
    return pd.DataFrame(rows)


def main():
    stores_df = gen_stores()
    products_df = gen_products()
    employees_df = gen_employees(stores_df)
    vendors_df = gen_vendors()
    campaigns_df = gen_campaigns()
    sales_df = gen_sales(stores_df, products_df)
    tickets_df = gen_support_tickets(stores_df)

    stores_df.to_csv(os.path.join(OUT_DIR, "stores.csv"), index=False)
    products_df.to_csv(os.path.join(OUT_DIR, "products.csv"), index=False)
    employees_df.to_csv(os.path.join(OUT_DIR, "employees.csv"), index=False)
    vendors_df.to_csv(os.path.join(OUT_DIR, "vendors.csv"), index=False)
    campaigns_df.to_csv(os.path.join(OUT_DIR, "campaigns.csv"), index=False)
    sales_df.to_csv(os.path.join(OUT_DIR, "sales.csv"), index=False)
    tickets_df.to_csv(os.path.join(OUT_DIR, "support_tickets.csv"), index=False)

    print(f"Generated: {len(stores_df)} stores, {len(products_df)} products, "
          f"{len(employees_df)} employees, {len(vendors_df)} vendors, "
          f"{len(campaigns_df)} campaigns, {len(sales_df)} sales rows, "
          f"{len(tickets_df)} support tickets")
    print(f"CSV files written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
