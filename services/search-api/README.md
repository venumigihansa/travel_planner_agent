# Xotelo Search API

FastAPI hotel search service that wraps the Xotelo hotel pricing API (via RapidAPI) with a mock-data fallback. It provides a consistent hotel search interface for the travel planner UI and agent tools.

## Purpose
- Offer hotel listings for a destination with optional filters (price, rating, amenities).
- Return hotel details and available room pricing when dates are provided.
- Provide a stable local API even when Xotelo is unavailable (mock data fallback).

## Setup

```bash
cd services/search-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
export XOTELO_API_KEY="your_rapidapi_key"
```

## Run

```bash
cd services/search-api
uvicorn app:app --host 0.0.0.0 --port 9084
```

## Notes
- Endpoints: `/hotels/search`, `/hotels/{hotel_id}`, `/hotels/{hotel_id}/availability`.
- `/hotels/search` returns a list of hotels plus metadata (total results, page, filters, data source).
- `/hotels/{hotel_id}` returns hotel details and room pricing when `checkInDate`/`checkOutDate` are provided.
- If `XOTELO_API_KEY` is missing or Xotelo calls fail, the service falls back to mock data in `services/search-api/data_mappings.py`.
- Logs indicate whether Xotelo or mock data was used.
