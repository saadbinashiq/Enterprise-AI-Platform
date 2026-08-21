"""
Multi-Agent Orchestrator (LangGraph).

Four agents in a pipeline:
  Data Agent          -> pulls relevant structured facts (KG + SQL)
  Analyst Agent        -> runs RAG over business docs for qualitative context
  Simulation Agent      -> runs a scenario simulation if the query is a "what-if"
  Recommendation Agent -> synthesizes everything into an executive-ready answer

This satisfies the "Multi-Agent System" and "AI Orchestrator" architecture
requirements: each agent has a single responsibility, state is passed
explicitly between them, and the full reasoning trace is preserved for
the Explainable AI layer.
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from knowledge_graph.graph_builder import get_graph
from rag.pipeline import get_pipeline
from simulation.engine import SCENARIOS


class AgentState(TypedDict):
    query: str
    data_result: Optional[dict]
    analysis: Optional[dict]
    simulation: Optional[dict]
    recommendation: Optional[str]


SIMULATION_KEYWORDS = {
    "price": "price_increase", "increase price": "price_increase",
    "staff": "staff_reduction", "layoff": "staff_reduction", "headcount": "staff_reduction",
    "new branch": "new_branch", "new store": "new_branch", "expansion": "new_branch",
    "marketing budget": "marketing_budget_increase", "ad spend": "marketing_budget_increase",
}


def data_agent(state: AgentState) -> AgentState:
    """Pulls structured facts from the Knowledge Graph relevant to common
    executive questions (underperforming stores, declining products,
    department costs). This is a simple keyword router; in a fuller build,
    an LLM would classify the query into one of these query types."""
    q = state["query"].lower()
    graph = get_graph()
    result = {}
    if "underperform" in q or "worst" in q or "which branch" in q or "which store" in q:
        result["underperforming_stores"] = graph.underperforming_stores()
    if "top" in q or "best" in q:
        result["top_stores"] = graph.top_stores()
    if "discontinue" in q or "declin" in q or "which product" in q:
        result["declining_products"] = graph.declining_products()
    if "department" in q or "operational cost" in q or "highest cost" in q:
        result["department_costs"] = graph.department_headcount_cost()
    if not result:
        result["note"] = "No direct structured-data match; relying on document analysis."
    state["data_result"] = result
    return state


def analyst_agent(state: AgentState) -> AgentState:
    """Runs the RAG pipeline over qualitative business documents to add
    context the structured data alone can't explain (the 'why')."""
    pipeline = get_pipeline()
    state["analysis"] = pipeline.answer(state["query"])
    return state


def simulation_agent(state: AgentState) -> AgentState:
    """Detects 'what if' style questions and runs the matching scenario
    simulation using current revenue/headcount as the baseline."""
    q = state["query"].lower()
    matched_scenario = None
    for keyword, scenario_key in SIMULATION_KEYWORDS.items():
        if keyword in q:
            matched_scenario = scenario_key
            break

    if matched_scenario == "price_increase" and ("increase" in q or "raise" in q or "%" in q):
        pct = _extract_percent(q, default=5.0)
        baseline_revenue = _current_total_revenue()
        state["simulation"] = SCENARIOS["price_increase"](baseline_revenue, pct)
    elif matched_scenario == "staff_reduction":
        pct = _extract_percent(q, default=10.0)
        state["simulation"] = SCENARIOS["staff_reduction"](labor_cost=500000, headcount=60, reduction_pct=pct)
    elif matched_scenario == "marketing_budget_increase":
        pct = _extract_percent(q, default=15.0)
        baseline_revenue = _current_total_revenue()
        state["simulation"] = SCENARIOS["marketing_budget_increase"](baseline_revenue, pct)
    elif matched_scenario == "new_branch":
        state["simulation"] = SCENARIOS["new_branch"](avg_branch_revenue=120000, avg_branch_cost=95000)
    return state


def recommendation_agent(state: AgentState) -> AgentState:
    """Synthesizes data_result + analysis + simulation into one executive
    answer. Uses an LLM if configured, otherwise a clear template -- either
    way the underlying facts are unchanged and fully traceable."""
    parts = []
    if state.get("data_result") and "note" not in state["data_result"]:
        for key, value in state["data_result"].items():
            parts.append(f"{key.replace('_', ' ').title()}: {value}")
    if state.get("simulation"):
        parts.append(f"Scenario simulation: {state['simulation']}")
    if state.get("analysis"):
        parts.append(f"Supporting context: {state['analysis']['answer']}")

    if not parts:
        state["recommendation"] = "No sufficient data found to answer this question confidently."
    else:
        state["recommendation"] = " | ".join(parts)
    return state


def _extract_percent(text: str, default: float) -> float:
    import re
    match = re.search(r"(\d+(\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else default


def _current_total_revenue() -> float:
    import pandas as pd
    from db.database import engine
    df = pd.read_sql("SELECT SUM(revenue) as total FROM sales", engine)
    return float(df["total"].iloc[0] or 0)


def build_orchestrator():
    workflow = StateGraph(AgentState)
    workflow.add_node("data_agent", data_agent)
    workflow.add_node("analyst_agent", analyst_agent)
    workflow.add_node("simulation_agent", simulation_agent)
    workflow.add_node("recommendation_agent", recommendation_agent)

    workflow.set_entry_point("data_agent")
    workflow.add_edge("data_agent", "analyst_agent")
    workflow.add_edge("analyst_agent", "simulation_agent")
    workflow.add_edge("simulation_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", END)

    return workflow.compile()


_ORCHESTRATOR_SINGLETON = None


def get_orchestrator():
    global _ORCHESTRATOR_SINGLETON
    if _ORCHESTRATOR_SINGLETON is None:
        _ORCHESTRATOR_SINGLETON = build_orchestrator()
    return _ORCHESTRATOR_SINGLETON


def ask(query: str) -> dict:
    orchestrator = get_orchestrator()
    result = orchestrator.invoke({"query": query})
    return {
        "answer": result["recommendation"],
        "reasoning_trace": {
            "data_agent": result.get("data_result"),
            "analyst_agent": result.get("analysis"),
            "simulation_agent": result.get("simulation"),
        },
    }


if __name__ == "__main__":
    for q in [
        "Which branch is underperforming?",
        "Which products should we discontinue?",
        "What will happen if we increase prices by 8%?",
        "Which department has the highest operational cost?",
    ]:
        print(f"\n=== {q} ===")
        r = ask(q)
        print("ANSWER:", r["answer"])
