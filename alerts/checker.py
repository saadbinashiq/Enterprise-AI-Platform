"""
Alert Center - threshold-based monitoring over the warehouse data.
In production, run `check_all_alerts()` on a schedule (APScheduler / cron)
and push results to the dashboard and/or a notification channel.
"""
import pandas as pd
from db.database import engine


def check_revenue_drop(threshold_pct: float = -10.0) -> list:
    sales = pd.read_sql("SELECT store_id, date, revenue FROM sales", engine)
    sales["date"] = pd.to_datetime(sales["date"])
    max_date = sales["date"].max()
    # drop the most recent partial week so week-over-week deltas aren't skewed
    sales = sales[sales["date"] <= max_date - pd.Timedelta(days=max_date.dayofweek + 1)]
    sales["week"] = sales["date"].dt.isocalendar().week
    weekly = sales.groupby(["store_id", "week"])["revenue"].sum().reset_index()

    alerts = []
    for store_id, group in weekly.groupby("store_id"):
        group = group.sort_values("week")
        if len(group) < 2:
            continue
        last, prev = group["revenue"].iloc[-1], group["revenue"].iloc[-2]
        if prev == 0:
            continue
        change_pct = (last - prev) / prev * 100
        if change_pct <= threshold_pct:
            alerts.append({"type": "Revenue Drop", "severity": "high",
                            "store_id": int(store_id), "change_pct": round(change_pct, 1)})
    return alerts


def check_stock_shortage_risk(reorder_threshold_units: int = 50) -> list:
    """Simplified proxy: products whose recent daily sales velocity would
    deplete a nominal on-hand stock level within 3 days."""
    sales = pd.read_sql("SELECT product_id, date, quantity FROM sales", engine)
    sales["date"] = pd.to_datetime(sales["date"])
    recent = sales[sales["date"] >= sales["date"].max() - pd.Timedelta(days=7)]
    velocity = recent.groupby("product_id")["quantity"].sum() / 7

    alerts = []
    for product_id, daily_qty in velocity.items():
        if daily_qty * 3 > reorder_threshold_units:
            alerts.append({"type": "Stock Shortage Risk", "severity": "medium",
                            "product_id": int(product_id), "avg_daily_units": round(daily_qty, 1)})
    return alerts[:10]  # cap for demo readability


def check_support_ticket_spike(threshold: int = 20) -> list:
    tickets = pd.read_sql("SELECT store_id, issue_type FROM support_tickets", engine)
    counts = tickets.groupby("store_id").size()
    return [{"type": "Customer Churn Risk", "severity": "medium",
             "store_id": int(store_id), "ticket_count": int(count)}
            for store_id, count in counts.items() if count >= threshold]


def check_all_alerts() -> dict:
    return {
        "revenue_drops": check_revenue_drop(),
        "stock_shortage_risks": check_stock_shortage_risk(),
        "support_spikes": check_support_ticket_spike(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(check_all_alerts(), indent=2))
