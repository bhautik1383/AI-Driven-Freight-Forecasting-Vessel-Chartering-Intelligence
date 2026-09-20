# Architecture decisions

## Decision pipeline

`Data sources → ETL → time-series storage → forecast → deterministic port check → landed-cost optimizer → ranked recommendation → explanation → planner approval`

The application preserves a strict separation between predictive models and safety rules. Freight prediction can use XGBoost, CatBoost, Prophet or ARIMA. Port draft compatibility remains a deterministic, auditable rule so a planner can inspect clearance and operational caveats.

## Frontend

Next.js with React and TypeScript hosts the operational workspaces. Recharts renders the forecast interaction and MapLibre supplies the primary vessel map. If map tiles cannot load, the application uses an explicitly labelled operational route plot instead of pretending it is a geographic map. A WebSocket updates demo vessel position and telemetry; `prefers-reduced-motion` disables non-essential motion.

## Backend

FastAPI defines the UI-facing REST and WebSocket contracts. In demo mode, it returns seeded but internally consistent values. Production adapters belong behind the FastAPI boundary, where credentials never cross into the browser. The deterministic assistant returns answers derived from the same API calculations. An Anthropic-backed tool layer can be enabled with `ANTHROPIC_API_KEY` after organizational review.

## Data and production controls

PostgreSQL plus TimescaleDB retains vessel positions and freight time series. Redis supports connector caching and WebSocket fan-out. A production deployment should retain each request, model version, input snapshot, constraint result and human decision as an audit record. Commercial AIS, Baltic Exchange and official-port connector fields must be normalized and data-quality-checked before model use.

## Demo integrity

The prototype clearly labels synthetic traffic as **DEMO / SIMULATED DATA**. It makes no claim that it accesses live AIS, Baltic Exchange, DGCIS or government port feeds. The interface supports credible demonstrations while preserving the contract boundary required for production integration.
