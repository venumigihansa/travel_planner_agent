# Python Booking API

FastAPI version of the hotel booking service. It loads the same mock data from the Ballerina `data_mappings.bal` file.

## Setup

```bash
cd o2-business-apis-python/booking-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd o2-business-apis-python/booking-api
uvicorn app:app --host 0.0.0.0 --port 9081
```

## Notes
- Data is read from `o2-business-apis-python/booking-api/data_mappings.py`.
- CORS is configured for `http://localhost:3001`.
- `x-jwt-assertion` is required for auth-protected endpoints (`/auth/profile`, `/bookings`, `/bookings/{id}`).
