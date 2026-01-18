# Amadeus Search API

FastAPI hotel search service that uses Amadeus Self-Service APIs with a mock-data fallback.

## Setup

```bash
cd o2-business-apis-python/amadeus-search-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
export AMADEUS_API_BASE_URL="https://test.api.amadeus.com"
export AMADEUS_API_KEY="your_key"
export AMADEUS_API_SECRET="your_secret"
```

## Run

```bash
cd o2-business-apis-python/amadeus-search-api
uvicorn app:app --host 0.0.0.0 --port 9084
```

## Notes
- Endpoints match the mock search API: `/hotels/search`, `/hotels/{hotel_id}`, `/hotels/{hotel_id}/availability`.
- If Amadeus credentials are missing or calls fail, the service falls back to mock data from `o2-business-apis-python/amadeus-search-api/data_mappings.py`.
- Logs indicate whether Amadeus or mock data was used.
