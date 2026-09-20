# NaviCast

NaviCast is Freightara's SIH26006 decision-intelligence prototype for forecasting overseas bulk-cargo freight, validating East Coast port constraints, comparing total landed cost and presenting a human-approved charter recommendation.

## What is included

- `frontend/` Next.js + TypeScript product interface, Recharts forecasting view and MapLibre vessel map.
- `backend/` FastAPI contracts: `/health`, `/vessels`, `/ports`, `/freight/forecast`, `/ports/check`, `/procurement`, `/charter/recommendation`, `/explain`, `/dashboard`, `/assistant/ask`, and WebSocket `/ws/live`.
- `database/schema.sql` PostgreSQL/TimescaleDB schema for a production data layer.

## Demo data disclosure

The application starts in **DEMO / SIMULATED DATA** mode. Vessel positions, freight rates, costs, ETA values and alerts are realistic seeded demo data, not live AIS, Baltic Exchange, port-authority or government data. The status surface labels every connector honestly. Configure commercial connectors only in the backend.

## Run locally

Prerequisites: Node.js 20+ and Python 3.11+.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. The FastAPI docs are at `http://localhost:8000/docs`.

## Environment

Copy `backend/.env.example` to `backend/.env` before configuring production connectors. Keep `AIS_API_KEY`, `BALTIC_EXCHANGE_API_KEY`, database credentials and `ANTHROPIC_API_KEY` on the backend only. Do not publish them as `NEXT_PUBLIC_*` variables.

Copy `frontend/.env.example` to `frontend/.env.local`; the default points to the local API.

## Production pathway

1. Deploy the Next.js frontend behind HTTPS and set `NEXT_PUBLIC_API_URL` to the API's public HTTPS base URL.
2. Run FastAPI behind a reverse proxy with WebSocket upgrade support.
3. Apply `database/schema.sql` to PostgreSQL with TimescaleDB and add Redis for caching, queues and live fan-out.
4. Build authenticated AIS, Baltic Exchange, port authority, DGCIS, commodity and FX connector adapters. Normalize their payloads through ETL before feeding model training.
5. Replace the seeded model input with approved time-series data, register model versions and retain every recommendation's input snapshot for audit.
6. Put charter approval behind organizational RBAC and an immutable decision record. NaviCast supports planners; it must not autonomously award a charter.

## SIH demo

Select **Start 2-minute demo**. It walks through the full narrative:

`Requirement → forecast → vessels → draft check → landed cost → ranked recommendation → explanation → human approval`

Use `Ctrl/Cmd + K` to jump between operational workspaces.
