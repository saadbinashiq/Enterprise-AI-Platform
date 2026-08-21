"""
Executive Dashboard + AI Executive Copilot (Streamlit).

Run:  streamlit run dashboard/app.py
Requires the API server running: uvicorn api.main:app --port 8000
"""
import os
import json
import requests
import streamlit as st
import pandas as pd

def _get_api_base() -> str:
    try:
        if "API_BASE" in st.secrets:
            return st.secrets["API_BASE"]
    except Exception:
        pass  # no secrets.toml present (normal for local runs) -- fall through
    return os.getenv("API_BASE", "http://localhost:8000")


API_BASE = _get_api_base()

st.set_page_config(
    page_title="Enterprise AI Decision Intelligence",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theming
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Lexend:wght@600;700;800;900&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    :root {
        --bg: #0B0F1A;
        --surface: #141B2D;
        --surface-2: #1B2438;
        --accent: #6366F1;
        --accent-2: #22D3EE;
        --border: #2A3550;
        --text: #F1F5F9;
        --text-muted: #94A3B8;
    }

    .stApp { background: var(--bg); }
    .main .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px; }

    /* base text */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: var(--text);
    }
    .stMarkdown, .stCaption, p { font-size: 1.02rem; }

    /* st.json renders its own light-background tree viewer -- don't force
       our light text color onto it, or the text becomes unreadable */
    div[data-testid="stJson"],
    div[data-testid="stJson"] * {
        color: initial !important;
    }

    /* ---- Hero header ---- */
    .hero {
        background: radial-gradient(circle at 15% 20%, #2E2A6B 0%, #14183A 55%, #0B0F1A 100%);
        padding: 2.5rem 2.7rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        border: 1px solid var(--border);
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
    }
    .hero::before {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(99,102,241,0.5) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero::after {
        content: "";
        position: absolute;
        bottom: -80px; left: 10%;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(34,211,238,0.3) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-eyebrow {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #C7D2FE;
        background: rgba(99, 102, 241, 0.22);
        border: 1px solid rgba(199, 210, 254, 0.35);
        padding: 0.32rem 0.8rem;
        border-radius: 999px;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    .hero h1 {
        font-family: 'Lexend', sans-serif;
        font-size: 2.3rem;
        font-weight: 900;
        margin: 0 0 0.6rem 0;
        color: white;
        letter-spacing: -0.01em;
        position: relative;
        z-index: 1;
    }
    .hero p {
        margin: 0;
        color: #CBD5E1;
        font-size: 1.08rem;
        font-weight: 500;
        max-width: 660px;
        position: relative;
        z-index: 1;
    }

    /* ---- KPI metrics ---- */
    div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.2rem 1.4rem 1.1rem 1.4rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }
    div[data-testid="stMetric"]:hover { box-shadow: 0 10px 26px rgba(0, 0, 0, 0.4); transform: translateY(-2px); }
    div[data-testid="stMetricLabel"] { font-weight: 700; color: var(--text-muted); font-size: 0.95rem; }
    div[data-testid="stMetricValue"] { font-weight: 900; color: var(--text); font-family: 'Lexend', sans-serif; font-size: 2rem; }

    /* ---- Section titles ---- */
    .section-title {
        font-family: 'Lexend', sans-serif;
        font-weight: 800;
        font-size: 1.3rem;
        color: var(--text);
        margin: 2.2rem 0 0.9rem 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding-bottom: 0.7rem;
        border-bottom: 1px solid var(--border);
    }
    .section-title .icon-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px; height: 32px;
        border-radius: 9px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
        font-size: 0.95rem;
    }

    /* ---- Cards ---- */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }
    .card-label {
        font-weight: 800;
        font-size: 1.05rem;
        color: var(--text);
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* ---- Badges ---- */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.04em;
    }
    .badge-high { background: rgba(248, 113, 113, 0.18); color: #FCA5A5; border: 1px solid rgba(248,113,113,0.35); }
    .badge-medium { background: rgba(251, 191, 36, 0.18); color: #FCD34D; border: 1px solid rgba(251,191,36,0.35); }
    .badge-low { background: rgba(74, 222, 128, 0.18); color: #86EFAC; border: 1px solid rgba(74,222,128,0.35); }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 10px 10px 0 0;
        font-weight: 700;
        font-size: 1rem;
        padding: 0 1.2rem;
        color: var(--text-muted);
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-2) !important;
        background: linear-gradient(180deg, rgba(99,102,241,0.15) 0%, rgba(99,102,241,0.0) 100%);
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent-2) !important; }

    /* ---- Copilot answer box ---- */
    .answer-box {
        background: linear-gradient(135deg, rgba(99,102,241,0.16) 0%, rgba(34,211,238,0.10) 100%);
        border: 1px solid rgba(99,102,241,0.4);
        border-left: 4px solid var(--accent-2);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-top: 0.6rem;
        font-size: 1.08rem;
        font-weight: 500;
        line-height: 1.65;
        color: var(--text);
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        color: white;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent) 0%, #8B5CF6 100%);
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.45);
    }

    /* ---- Inputs ---- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        font-size: 1rem !important;
    }

    /* ---- Dataframes ---- */
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }

    /* ---- Alert tables (HTML) ---- */
    .alert-table { width: 100%; border-collapse: collapse; font-size: 1rem; }
    .alert-table th {
        text-align: left; background: var(--surface-2); color: var(--text-muted);
        font-weight: 700; padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--border);
    }
    .alert-table td {
        padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--border);
        color: var(--text); font-weight: 500; background: var(--surface);
    }

    /* ---- st.info / st.error / st.success boxes ---- */
    div[data-testid="stAlert"] { font-size: 1.02rem; font-weight: 500; }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: #070A12;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    section[data-testid="stSidebar"] h3 { font-weight: 800 !important; font-size: 1.1rem !important; }
    section[data-testid="stSidebar"] hr { border-color: var(--border); }
</style>
""", unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    css_class = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}.get(severity, "badge-medium")
    return f'<span class="badge {css_class}">{severity.upper()}</span>'


def section_title(icon: str, text: str):
    st.markdown(f'<div class="section-title"><span class="icon-chip">{icon}</span> {text}</div>', unsafe_allow_html=True)


def render_alert_table(df: pd.DataFrame, empty_msg: str):
    if df.empty:
        st.info(empty_msg)
        return
    df = df.copy()
    df["severity"] = df["severity"].apply(severity_badge)
    st.write(df.to_html(escape=False, index=False, classes="alert-table"), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <span class="hero-eyebrow">Developed by \u00b7 Saad Bin Ashiq</span>
    <h1>\U0001F4CA Enterprise AI Business Decision Intelligence Platform</h1>
    <p>Multi-agent knowledge graph, retrieval-augmented reasoning, and forecasting over your enterprise data — built for executives who need answers, not dashboards full of numbers.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### \u2699\ufe0f System Status")
    try:
        requests.get(f"{API_BASE}/", timeout=3)
        st.success("API connected")
    except requests.exceptions.RequestException:
        st.error("API not reachable")
        st.caption(f"Expected at `{API_BASE}`")
    st.markdown("---")
    st.markdown("### \U0001F9E9 Architecture")
    st.caption(
        "\U0001F578\ufe0f Knowledge Graph\n\n"
        "\U0001F4DA RAG Pipeline\n\n"
        "\U0001F4C8 Forecasting Engine\n\n"
        "\U0001F52E Scenario Simulation\n\n"
        "\U0001F916 Multi-Agent Orchestrator\n\n"
        "\U0001F6A8 Alert Center"
    )
    st.markdown("---")
    st.caption("Built with FastAPI \u00b7 LangGraph \u00b7 Streamlit")

tab_dashboard, tab_copilot, tab_simulate, tab_alerts = st.tabs(
    ["\U0001F4C8  Executive Dashboard", "\U0001F916  AI Copilot", "\U0001F52E  Scenario Simulation", "\U0001F6A8  Alert Center"]
)

# ---------------- Executive Dashboard ----------------
with tab_dashboard:
    try:
        kpis = requests.get(f"{API_BASE}/dashboard/kpis").json()
        col1, col2, col3 = st.columns(3)
        col1.metric("\U0001F4B0  Total Revenue", f"${kpis['total_revenue']:,.0f}")
        col2.metric("\U0001F4CA  Avg Product Margin", f"{kpis['avg_product_margin_pct']:.1f}%")
        col3.metric("\U0001F465  Total Labor Cost", f"${kpis['total_labor_cost']:,.0f}")

        section_title("\U0001F3C6", "Top vs Underperforming Stores")
        c1, c2 = st.columns(2)
        top = pd.DataFrame(requests.get(f"{API_BASE}/analyst/top-stores").json())
        under = pd.DataFrame(requests.get(f"{API_BASE}/analyst/underperforming-stores").json())
        with c1:
            st.markdown('<div class="card"><div class="card-label">\u2705 Top Stores</div>', unsafe_allow_html=True)
            st.dataframe(top, hide_index=True, width='stretch')
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="card"><div class="card-label">\u26a0\ufe0f Underperforming Stores</div>', unsafe_allow_html=True)
            st.dataframe(under, hide_index=True, width='stretch')
            st.markdown('</div>', unsafe_allow_html=True)

        section_title("\U0001F4E6", "Declining Products (discontinuation candidates)")
        declining = pd.DataFrame(requests.get(f"{API_BASE}/analyst/declining-products").json())
        st.dataframe(declining, hide_index=True, width='stretch')

        section_title("\U0001F465", "Department Headcount / Cost")
        dept = pd.DataFrame(requests.get(f"{API_BASE}/analyst/department-costs").json())
        st.bar_chart(dept.set_index("department")["total_cost"], color="#818CF8")

        section_title("\U0001F4C9", "Revenue Forecast (next 30 days)")
        forecast = pd.DataFrame(requests.get(f"{API_BASE}/forecast/revenue?periods=30").json())
        forecast["ds"] = pd.to_datetime(forecast["ds"])
        st.line_chart(forecast.set_index("ds")[["yhat", "yhat_lower", "yhat_upper"]])
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the API. Start it with: `uvicorn api.main:app --port 8000`")

# ---------------- AI Copilot ----------------
with tab_copilot:
    st.markdown(
        "Ask a business question, e.g. *\u201cWhich branch is underperforming?\u201d* or "
        "*\u201cWhat will happen if we increase prices by 8%?\u201d*"
    )
    question = st.text_input("Your question:", placeholder="Type a business question...")
    if st.button("\U0001F50D  Ask", type="primary") and question:
        with st.spinner("Running multi-agent analysis..."):
            resp = requests.post(f"{API_BASE}/copilot/ask", json={"question": question}).json()
        st.markdown("#### \U0001F4A1 Answer")
        st.markdown(f'<div class="answer-box">{resp["answer"]}</div>', unsafe_allow_html=True)
        with st.expander("\U0001F9E9 Reasoning trace (Explainable AI)"):
            st.json(resp["reasoning_trace"])

# ---------------- Scenario Simulation ----------------
with tab_simulate:
    scenario = st.selectbox("Scenario", ["price_increase", "staff_reduction",
                                          "new_branch", "marketing_budget_increase"])
    st.caption("Provide parameters as JSON, e.g. for price_increase: "
               '`{"current_revenue": 1000000, "pct_increase": 5}`')
    params_text = st.text_area("Parameters (JSON)", value='{"current_revenue": 1000000, "pct_increase": 5}')
    if st.button("\u25b6\ufe0f  Run Simulation", type="primary"):
        try:
            params = json.loads(params_text)
            result = requests.post(f"{API_BASE}/simulate",
                                    json={"scenario": scenario, "params": params}).json()
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.json(result)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- Alert Center ----------------
with tab_alerts:
    alerts = requests.get(f"{API_BASE}/alerts").json()

    section_title("\U0001F4C9", "Revenue Drop Alerts")
    render_alert_table(pd.DataFrame(alerts["revenue_drops"]), "No revenue drop alerts.")

    section_title("\U0001F4E6", "Stock Shortage Risks")
    df = pd.DataFrame(alerts["stock_shortage_risks"])
    if not df.empty:
        st.dataframe(df, hide_index=True, width='stretch')
    else:
        st.info("No stock shortage risks.")

    section_title("\U0001F4DE", "Customer Churn Risk (support ticket spikes)")
    render_alert_table(pd.DataFrame(alerts["support_spikes"]), "No churn risk alerts.")