# Travel Planner Frontend

React UI for the Lab 02 travel planner demo. It talks to the agent `/travelPlanner/chat` endpoint and the hotel APIs.

## Prerequisites

- Node.js 22+
- npm

## Configuration

Update `frontend/.env` as needed:

```bash
PORT=3001
REACT_APP_CHAT_API_URL=http://localhost:9090/travelPlanner
REACT_APP_HOTEL_API_BASE_URL=http://localhost:9090
REACT_APP_API_BASE_URL=http://localhost:9090
REACT_APP_CLERK_PUBLISHABLE_KEY=pk_test_...
```

`REACT_APP_HOTEL_API_BASE_URL` is optional; it defaults to `http://localhost:9090`.
`REACT_APP_API_BASE_URL` is the FastAPI agent base URL for profile endpoints.
`REACT_APP_CLERK_PUBLISHABLE_KEY` comes from your Clerk dashboard under API Keys.

## Run

```bash
cd frontend
npm install
npm start
```

The app will be available at `http://localhost:3001`.
