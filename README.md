# Travel Planner Agent

This repo contains the minimal, clean Python + React stack needed to run the travel planner agent:

- **AI Agent (BFF)**: `ai_backends/agent/`
- **Business APIs (Python)**: merged into `ai_backends/agent/`
- **Frontend**: `frontend/`
- **Policy ingest (optional)**: `ai_backends/ingest/` + `ai_backends/ingest/policies/`
- **Postgres schema**: `resources/create_tables.sql`

## Prerequisites
- Python 3.10+
- Node.js 22+
- PostgreSQL (for personalization)
- Pinecone index (for hotel policy retrieval)

## Quick Start (local)

### 0) Optional: Postgres personalization table
```bash
psql -d travel_planner -f resources/create_tables.sql
```

### 1) Start the AI agent (BFF)
Follow `ai_backends/agent/README.md` to set up `.env` and run:

```bash
cd ai_backends/agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9090
```

### 2) Start the frontend
Follow `frontend/README.md` to set up `.env`, then:

```bash
cd frontend
npm install
npm start
```

## Optional: Seed Pinecone policies
If you need to populate Pinecone from scratch:

```bash
cd ai_backends/ingest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
```

## Notes
- `.env` files are intentionally excluded from this repo. Create them from the READMEs in each folder.
- The agent now serves hotel search and booking endpoints directly on port 9090.
- Clerk authentication is required for user profile endpoints; configure `CLERK_JWKS_URL` (and optional `CLERK_ISSUER`/`CLERK_AUDIENCE`) in the agent `.env`, plus `REACT_APP_CLERK_PUBLISHABLE_KEY` in the frontend.
