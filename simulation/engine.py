"""
Scenario Simulation Engine - "what if" business simulations.

These are deliberately simple, transparent, assumption-based models (not
fitted econometric models) so they're easy to explain in a report or demo.
Document the assumed constants clearly in your presentation as illustrative,
not empirically fitted -- that transparency is a strength, not a gap.
"""


def simulate_price_increase(current_revenue: float, pct_increase: float, elasticity: float = -1.2) -> dict:
    """
    elasticity: assumed price elasticity of demand (negative = demand falls
    as price rises). -1.2 means a 1% price rise causes a 1.2% demand drop --
    a common illustrative retail assumption.
    """
    demand_change_pct = elasticity * pct_increase
    projected_revenue = current_revenue * (1 + pct_increase / 100) * (1 + demand_change_pct / 100)
    return {
        "scenario": f"Price increase of {pct_increase}%",
        "current_revenue": round(current_revenue, 2),
        "projected_revenue": round(projected_revenue, 2),
        "delta_pct": round((projected_revenue - current_revenue) / current_revenue * 100, 2),
        "assumption": f"demand elasticity = {elasticity}",
    }


def simulate_staff_reduction(labor_cost: float, headcount: int, reduction_pct: float,
                              productivity_loss_per_head_pct: float = 3.0) -> dict:
    new_headcount = headcount * (1 - reduction_pct / 100)
    cost_savings = labor_cost * (reduction_pct / 100)
    est_productivity_loss_pct = reduction_pct * (productivity_loss_per_head_pct / 100)
    return {
        "scenario": f"Staff reduction of {reduction_pct}%",
        "current_headcount": headcount,
        "new_headcount": round(new_headcount),
        "monthly_cost_savings": round(cost_savings, 2),
        "estimated_productivity_loss_pct": round(est_productivity_loss_pct, 2),
        "assumption": f"{productivity_loss_per_head_pct}% productivity loss per 1% headcount cut",
    }


def simulate_new_branch(avg_branch_revenue: float, avg_branch_cost: float, ramp_up_months: int = 6) -> dict:
    monthly_net = avg_branch_revenue - avg_branch_cost
    breakeven_month = None
    cumulative = 0
    for m in range(1, 25):
        ramp_factor = min(1.0, m / ramp_up_months)
        cumulative += monthly_net * ramp_factor
        if cumulative > 0 and breakeven_month is None:
            breakeven_month = m
    return {
        "scenario": "New branch opening",
        "avg_monthly_net_at_maturity": round(monthly_net, 2),
        "estimated_breakeven_month": breakeven_month,
        "assumption": f"{ramp_up_months}-month linear ramp-up to full productivity",
    }


def simulate_marketing_budget_increase(current_revenue: float, budget_increase_pct: float,
                                        roas: float = 3.0, diminishing_returns: float = 0.7) -> dict:
    """
    roas: assumed return on ad spend (revenue generated per $ spent) at
    current budget level. diminishing_returns discounts marginal spend to
    reflect typically lower incremental returns.
    """
    incremental_revenue_pct = budget_increase_pct * roas * diminishing_returns / 100
    projected_revenue = current_revenue * (1 + incremental_revenue_pct)
    return {
        "scenario": f"Marketing budget increase of {budget_increase_pct}%",
        "current_revenue": round(current_revenue, 2),
        "projected_revenue": round(projected_revenue, 2),
        "delta_pct": round((projected_revenue - current_revenue) / current_revenue * 100, 2),
        "assumption": f"assumed ROAS={roas}, diminishing returns factor={diminishing_returns}",
    }


SCENARIOS = {
    "price_increase": simulate_price_increase,
    "staff_reduction": simulate_staff_reduction,
    "new_branch": simulate_new_branch,
    "marketing_budget_increase": simulate_marketing_budget_increase,
}
