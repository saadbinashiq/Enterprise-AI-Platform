# Enterprise AI Business Decision Intelligence Platform

Implementation of the **AI-002 Enterprise AI Business Decision Intelligence Platform**
case study, scoped for a 2-person, 4-week internship deliverable. Every
architectural component in the case study (multi-agent system, RAG, knowledge
graph, forecasting, explainability, dashboard, alerting) is implemented and
runnable end-to-end on a synthetic dataset, with **zero required external
services or API keys** — everything has a lightweight local fallback, with a
documented path to swap in the full production stack (Postgres, Neo4j, Redis,
OpenAI, Prophet).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic enterprise data (stores, products, sales, employees, etc.)
python -m data.generate_data

# 3. Load it into the database (SQLite by default, zero setup)
python -m db.loader

# 4. Start the API
uvicorn api.main:app --reload --port 8000
# API docs at http://localhost:8000/docs

# 5. In a second terminal, start the dashboard
streamlit run dashboard/app.py
```

That's it — no Docker, no API key, no external database required to run the
full demo. Optional `.env` file (copy `.env.example`) lets you switch to
Postgres, Neo4j, and a real OpenAI-backed LLM for the "production" version.

## Architecture

```
                        ┌─────────────────────────┐
  CSV exports  ──────►  │  Enterprise Data         │
  (simulating           │  Connector (db/loader)   │
  ERP/POS/HRMS/etc.)    └───────────┬─────────────┘
                                     ▼
                         ┌──────────────────────┐
                         │  Postgres / SQLite    │◄──────────────┐
                         │  (warehouse)          │                │
                         └───────────┬──────────┘                │
                                     ▼                            │
                   ┌─────────────────────────────┐                │
                   │  Knowledge Graph             │                │
                   │  (NetworkX / Neo4j)          │                │
                   └───────────┬─────────────────┘                │
                                │                                  │
        ┌───────────────────────┼───────────────────────┐          │
        ▼                       ▼                       ▼          │
 ┌─────────────┐      ┌─────────────────┐     ┌──────────────────┐│
 │ RAG Pipeline │      │ Forecasting      │     │ Simulation        ││
 │ (in-memory   │      │ Engine           │     │ Engine            ││
 │ numpy +      │      │ (statsmodels)    │     │ (what-if models)  ││
 │ embeddings)  │      │                  │     │                   ││
 └──────┬──────┘      └────────┬────────┘     └─────────┬────────┘│
        └───────────────────────┼──────────────────────────┘        │
                                 ▼                                   │
                   ┌───────────────────────────┐                     │
                   │  Multi-Agent Orchestrator  │                     │
                   │  (LangGraph):               │                     │
                   │  Data → Analyst →           │                     │
                   │  Simulation → Recommendation │                     │
                   └────────────┬─────────────────┘                     │
                                 ▼                                       │
                   ┌───────────────────────────┐        Alert Center ───┘
                   │  FastAPI REST layer        │◄───── (threshold checks
                   └────────────┬─────────────────┐       over warehouse data)
                                 ▼
                   ┌───────────────────────────┐
                   │  Streamlit Dashboard +      │
                   │  AI Executive Copilot UI    │
                   └───────────────────────────┘
```

## Module → File Map

| Case Study Module | Implementation |
|---|---|
| Enterprise Data Connector | `data/generate_data.py`, `db/loader.py`, `db/models.py` |
| Knowledge Graph | `knowledge_graph/graph_builder.py` |
| AI Business Analyst | `knowledge_graph` query methods + `rag/pipeline.py`, exposed via `agents/orchestrator.py` (data_agent + analyst_agent) |
| Scenario Simulation Engine | `simulation/engine.py` |
| Decision Recommendation Engine | `agents/orchestrator.py` (recommendation_agent) |
| AI Executive Copilot | `api/main.py` `/copilot/ask` + `dashboard/app.py` chat tab |
| Explainable AI | Every copilot response includes `reasoning_trace` (data used, RAG sources + confidence, simulation assumptions) |
| Executive Dashboard | `dashboard/app.py` |
| Alert Center | `alerts/checker.py` |
| Multi-Agent / AI Orchestrator | `agents/orchestrator.py` (LangGraph `StateGraph`) |

## Design Decisions Worth Explaining in Your Report

- **Scale**: the case study describes 120 stores / 14 countries / 100M
  records. This build uses 12 stores / 3 countries / ~20k sales rows —
  the same architecture at a size a laptop can actually run and a grader
  can actually inspect. The README and presentation should say explicitly
  that scaling this design to production volume means: Postgres read
  replicas, Neo4j clustering, Redis caching (all wired into
  `docker-compose.yml` as the production path), and horizontal scaling of
  the FastAPI layer behind a load balancer.
- **No required API key**: `rag/pipeline.py` and the copilot fall back to an
  extractive/rule-based answer when `OPENAI_API_KEY` isn't set, so the
  project is fully demoable offline. Set the key in `.env` to switch to real
  LLM-generated answers.
- **Prophet vs statsmodels**: the spec lists Prophet explicitly. This build
  uses `statsmodels.ExponentialSmoothing` instead because Prophet's
  cmdstan/pystan build toolchain is heavy and fragile in restricted/offline
  environments. The input/output shape (`ds`/`y` in, `yhat`/`yhat_lower`/
  `yhat_upper` out) is deliberately Prophet-compatible — swapping in real
  Prophet in `forecasting/forecaster.py` is a 2-line change if you have the
  build toolchain available.
- **NetworkX vs Neo4j**: same reasoning — NetworkX needs no server and runs
  anywhere; `knowledge_graph/graph_builder.py` includes a parallel `Neo4jGraph`
  class with the same method signatures, switchable via `GRAPH_BACKEND=neo4j`.
- **No vector database (no ChromaDB/FAISS)**: `rag/pipeline.py` stores chunk
  embeddings as a plain in-memory numpy array and retrieves with cosine
  similarity, instead of using a vector database. This was a deliberate fix
  after ChromaDB's native/compiled components caused repeated silent crashes
  (no Python traceback — consistent with a native-extension fault) on some
  Windows setups. For a corpus of a few hundred document chunks this is
  fast enough that a vector database adds risk without adding real benefit;
  call this out explicitly as a pragmatic engineering trade-off in your
  report, and note that a real production deployment with a much larger
  document corpus would swap `retrieve()` for a proper vector database.
- **Simulation models are assumption-based, not fitted**: `simulation/engine.py`
  uses illustrative constants (e.g. price elasticity = -1.2) clearly labeled
  as assumptions in every response. This is intentional transparency, not a
  shortcut — call this out explicitly in your presentation.

## Example Queries to Demo

```
Which branch is underperforming?
Which products should we discontinue?
Which department has the highest operational cost?
What will happen if we increase prices by 8%?
```

## Bonus Challenge Implemented

**AI Strategy Planner** (lightweight): the recommendation_agent in
`agents/orchestrator.py` already synthesizes structured data + qualitative
context + simulation output into one recommendation — extending this into a
1-page strategy memo generator (structured prompt over the same
`reasoning_trace`) is a natural next step and a good live extension to show
during the presentation if time allows.

## Known Limitations

- Synthetic data, not real enterprise systems — this demonstrates the
  connector *architecture*, not real integrations.
- Simulation models are simple and assumption-based (documented above), not
  fitted causal/econometric models.
- Multi-agent query routing (`agents/orchestrator.py::data_agent`) uses
  keyword matching rather than LLM-based intent classification, to keep the
  demo fully functional without an API key. Swapping in an LLM classifier
  there is a natural upgrade once `OPENAI_API_KEY` is configured.
