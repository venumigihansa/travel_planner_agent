# Python LangGraph Agent (OpenAI)

Python LangGraph travel planner agent with hotel search, bookings, and policy retrieval.

## Features
- Tool-calling agent for hotel search, booking, and policy queries
- Pinecone policy retrieval with OpenAI embeddings
- Chat endpoints at `/travelPlanner/chat` and `/travelPlanner/chat/sessions`
- Booking REST endpoints

## Setup

```bash
cd ai_backends/agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `ai_backends/agent/.env` (use `ai_backends/agent/.env.example` as a template):

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
PINECONE_API_KEY=...
PINECONE_SERVICE_URL=https://your-index.svc.your-region.pinecone.io
PINECONE_INDEX_NAME=hotel-policies
XOTELO_API_KEY=...
WEATHER_API_KEY=...
WEATHER_API_BASE_URL=http://api.weatherapi.com/v1
SERPER_API_KEY=...
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
```

Defaults if omitted:
- `OPENAI_MODEL=gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `PINECONE_INDEX_NAME=hotel-policies`

Optional (only if you use profile endpoints):

```bash
```

## Run

```bash
uvicorn app:app --host 0.0.0.0 --port 9090
```

## Notes
- `query_hotel_policy_tool` expects Pinecone metadata with a `content` field and `hotelId` filter, matching the ingest pipeline in `ai_backends/ingest/ingest.py`.
- `SERPER_API_KEY` is required for the web-search fallback when Pinecone has no policy matches.
- Hotel search and booking run inside the agent service; booking state is stored in `ai_backends/agent/data`.
