# Python LangGraph Migration (OpenAI)

This folder contains a Python LangGraph migration of the Ballerina travel planner agent.

## Features Parity
- Tool-calling agent for hotel search, booking, and policy queries
- Pinecone policy retrieval with OpenAI embeddings
- `/travelPlanner/chat` endpoint for the React frontend
- CORS settings mirroring the Ballerina service

## Setup

```bash
cd ai_backends/agent/python_migration
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with the required settings:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
USER_ID=user_john_001
USER_NAME=John Smith
PINECONE_API_KEY=...
PINECONE_SERVICE_URL=https://your-index.svc.your-region.pinecone.io
PINECONE_INDEX_NAME=travelagent3
HOTEL_SEARCH_API_URL=http://localhost:9083
BOOKING_API_URL=http://localhost:9081
WEATHER_API_KEY=...
WEATHER_API_BASE_URL=http://api.weatherapi.com/v1
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=travel_planner
PG_USER=postgres
PG_PASSWORD=...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
CLERK_ISSUER=https://<your-clerk-domain>
CLERK_AUDIENCE=...
```

Get the Clerk domain and publishable key from the Clerk dashboard (API Keys). Set `CLERK_JWKS_URL` to your instance JWKS URL (usually `https://<your-clerk-domain>/.well-known/jwks.json`). Use `CLERK_ISSUER` to match the token issuer, and set `CLERK_AUDIENCE` only if your tokens include an audience claim.

## Run

```bash
uvicorn app:app --host 0.0.0.0 --port 9090
```

## Notes
- `query_hotel_policy_tool` expects Pinecone metadata with a `content` field and `hotelId` filter, matching the ingest pipeline in `ai_backends/ingest/python/ingest.py`.
- The weather tool is a placeholder. Provide `WEATHER_MCP_URL` if you expose an HTTP wrapper for the MCP server.
- PostgreSQL is used for personalization. Initialize the `user_activities` table with `resources/create_tables.sql` in the repo root.
- Set `HOTEL_SEARCH_API_URL` and `BOOKING_API_URL` to either the Ballerina services (`o2-business-apis/`) or the Python services (`o2-business-apis-python/`).
