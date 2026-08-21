"""
Enterprise Data Connector.

In the real spec this connects to ERP / CRM / HRMS / POS / Inventory /
Finance / Marketing / Support systems. Here, each CSV plays the role of an
export from one of those systems:
    stores, products    <- ERP + POS
    employees           <- HRMS
    vendors             <- Finance/ERP (procurement)
    campaigns           <- Marketing
    sales               <- POS
    support_tickets     <- Customer Support platform

Everything downstream (knowledge graph, RAG, forecasting, agents) only reads
from the Postgres/SQLite tables built here -- so replacing a CSV loader with
a real system's API client later is a drop-in swap that doesn't touch any
other module.
"""
import os
import pandas as pd

from db.database import engine
from db.models import Base

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "csv")

TABLES = ["stores", "products", "employees", "vendors", "campaigns", "sales", "support_tickets"]
DATE_COLUMNS = {"date", "hire_date", "start_date", "end_date"}


def init_db():
    Base.metadata.create_all(engine)


def load_all(reset: bool = True):
    init_db()
    for table in TABLES:
        csv_path = os.path.join(CSV_DIR, f"{table}.csv")
        df = pd.read_csv(csv_path)
        for col in DATE_COLUMNS.intersection(df.columns):
            df[col] = pd.to_datetime(df[col]).dt.date
        df.to_sql(table, engine, if_exists=("replace" if reset else "append"), index=False)
        print(f"Loaded {len(df)} rows into '{table}'")


if __name__ == "__main__":
    load_all()
