# Travel Planner Agent

Minimal Python + React stack for the travel planner agent.

- **AI Agent**: `backend/agent/`
- **Booking API**: `backend/booking_api/`
- **Frontend**: `frontend/`
- **Policy ingest**: `resources/ingest/`
- **Sample policy PDFs**: `resources/policy_pdfs/`

## Quick Start

### Agent Manager deployment
Deploy the agent in your Agent Manager environment (details to be added). The flow below covers the required supporting services:

**Booking API**
- Runs locally on `http://localhost:9091` when started via `uvicorn`.
- You can also deploy it to a cloud host; just point the agent configuration at the deployed base URL.

**Pinecone policies (required)**
- Create a Pinecone index using your preferred embedding model.
- Set the Pinecone and embedding configuration in `resources/ingest/.env`.
- Run the ingest to populate the index (see "Seed Pinecone policies" below).

### Local development (optional)
Local requirements:
- Python 3.10+
- Node.js 22+
- Mock hotel dataset (local file)

#### 1) Start the AI agent
Create `backend/agent/.env` from `backend/agent/.env.example`, then:

```bash
cd backend/agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9090
```

#### 2) Start the booking API (local)
```bash
cd backend/booking_api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn booking_api:app --host 0.0.0.0 --port 9091
```

#### 3) Start the frontend (local)
Create `frontend/.env` as needed (see `frontend/README.md`), then:

```bash
cd frontend
npm install
npm start
```

## Seed Pinecone policies (required)
Populate Pinecone from the sample policies in `resources/policy_pdfs`.
Make sure you have created a Pinecone index with your preferred embedding model and set these values in `resources/ingest/.env`:
`PINECONE_SERVICE_URL`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, and optional chunk settings.

```bash
cd resources/ingest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingest.py
```

## Notes
- `.env` files are intentionally excluded from this repo.
- The agent serves chat at `http://localhost:9090/travelPlanner/chat`.
