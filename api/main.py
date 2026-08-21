"""
REST API for the Enterprise AI Business Decision Intelligence Platform.

Run:  uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from knowledge_graph.graph_builder import get_graph
from forecasting.forecaster import forecast_revenue
from simulation.engine import SCENARIOS
from alerts.checker import check_all_alerts
from agents.orchestrator import ask as agent_ask

app = FastAPI(
    title="Enterprise AI Business Decision Intelligence Platform",
    description="AI-002 case study implementation",
    version="1.0.0",
)


class CopilotQuery(BaseModel):
    question: str


class SimulationRequest(BaseModel):
    scenario: str  # one of: price_increase, staff_reduction, new_branch, marketing_budget_increase
    params: dict


@app.get("/")
def root():
    return {"status": "ok", "message": "Enterprise AI Decision Intelligence Platform API"}


@app.post("/copilot/ask")
def copilot_ask(q: CopilotQuery):
    """AI Executive Copilot - natural language business questions,
    routed through the multi-agent orchestrator."""
    return agent_ask(q.question)


@app.get("/analyst/underperforming-stores")
def underperforming_stores(bottom_n: int = 3):
    return get_graph().underperforming_stores(bottom_n)


@app.get("/analyst/top-stores")
def top_stores(top_n: int = 3):
    return get_graph().top_stores(top_n)


@app.get("/analyst/declining-products")
def declining_products(bottom_n: int = 3):
    return get_graph().declining_products(bottom_n)


@app.get("/analyst/department-costs")
def department_costs():
    return get_graph().department_headcount_cost()


@app.get("/forecast/revenue")
def revenue_forecast(store_id: int = None, periods: int = 30):
    df = forecast_revenue(store_id=store_id, periods=periods)
    df["ds"] = df["ds"].astype(str)
    return df.to_dict("records")


@app.post("/simulate")
def simulate(req: SimulationRequest):
    if req.scenario not in SCENARIOS:
        raise HTTPException(status_code=400,
                             detail=f"Unknown scenario. Choose from: {list(SCENARIOS.keys())}")
    return SCENARIOS[req.scenario](**req.params)


@app.get("/alerts")
def alerts():
    return check_all_alerts()


@app.get("/dashboard/kpis")
def dashboard_kpis():
    """Aggregated KPIs for the Executive Dashboard."""
    import pandas as pd
    from db.database import engine

    sales = pd.read_sql("SELECT revenue FROM sales", engine)
    products = pd.read_sql("SELECT price, cost FROM products", engine)
    employees = pd.read_sql("SELECT salary FROM employees", engine)

    total_revenue = float(sales["revenue"].sum())
    avg_margin_pct = float(((products["price"] - products["cost"]) / products["price"]).mean() * 100)
    total_labor_cost = float(employees["salary"].sum())

    return {
        "total_revenue": round(total_revenue, 2),
        "avg_product_margin_pct": round(avg_margin_pct, 2),
        "total_labor_cost": round(total_labor_cost, 2),
        "alerts_summary": check_all_alerts(),
    }
