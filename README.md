# Travel Planner Agent

Minimal Python + React stack for the travel planner agent.

- **AI Agent (BFF)**: `ai_backends/agent/`
- **Frontend**: `frontend/`
- **Policy ingest (optional)**: `ai_backends/ingest/`
- **Postgres schema**: `resources/create_tables.sql`
- **Sample policy PDFs**: `resources/policy_pdfs/`

## Prerequisites
- Python 3.10+
- Node.js 22+
- PostgreSQL (optional, for profile personalization)
- Pinecone index (optional, for hotel policy retrieval)
- Xotelo API key (for live hotel search/booking)

## Quick Start (local)

### 0) Optional: Postgres personalization table
```bash
psql -d travel_planner -f resources/create_tables.sql
```

### 1) Start the AI agent (BFF)
Create `ai_backends/agent/.env` from `ai_backends/agent/.env.example`, then:

```bash
cd ai_backends/agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9090
```

### 2) Start the frontend
Create `frontend/.env` as needed (see `frontend/README.md`), then:

```bash
cd frontend
npm install
npm start
```

## Optional: Seed Pinecone policies
Populate Pinecone from the sample policies in `resources/policy_pdfs`:

```bash
cd ai_backends/ingest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
```

## Notes
- `.env` files are intentionally excluded from this repo.
- The agent serves chat at `http://localhost:9090/travelPlanner/chat`.
- Profile endpoints require Asgardeo configuration (`ASGARDEO_JWKS_URL`, optional `ASGARDEO_ISSUER`/`ASGARDEO_AUDIENCE`) and Postgres. See `resources/create_tables.sql` for the schema.
