# Python Booking API

FastAPI version of the hotel booking service. It loads mock data from `data_mappings.py`.

## Setup

```bash
cd services/booking-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd services/booking-api
uvicorn app:app --host 0.0.0.0 --port 9081
```

## Notes
- Data is read from `services/booking-api/data_mappings.py`.
- CORS is configured for `http://localhost:3001`.
- `x-jwt-assertion` is required for auth-protected endpoints (`/auth/profile`, `/bookings`, `/bookings/{id}`).
