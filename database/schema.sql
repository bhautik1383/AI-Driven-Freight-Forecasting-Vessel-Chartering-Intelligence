CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE ports (id text PRIMARY KEY, name text NOT NULL, draft_limit_m numeric(4,1) NOT NULL, latitude numeric, longitude numeric, updated_at timestamptz DEFAULT now());
CREATE TABLE vessels (id text PRIMARY KEY, name text NOT NULL, vessel_type text, dwt integer, draft_m numeric(4,1), status text, last_position_at timestamptz);
CREATE TABLE vessel_positions (time timestamptz NOT NULL, vessel_id text REFERENCES vessels(id), latitude numeric NOT NULL, longitude numeric NOT NULL, speed_kn numeric, heading numeric, PRIMARY KEY (time, vessel_id));
SELECT create_hypertable('vessel_positions', 'time', if_not_exists => TRUE);
CREATE TABLE freight_rates (time timestamptz NOT NULL, route text NOT NULL, commodity text NOT NULL, vessel_type text NOT NULL, rate_usd_per_t numeric NOT NULL, source text NOT NULL, PRIMARY KEY(time, route, commodity, vessel_type));
SELECT create_hypertable('freight_rates', 'time', if_not_exists => TRUE);
CREATE TABLE decision_runs (id uuid PRIMARY KEY, created_at timestamptz DEFAULT now(), request jsonb NOT NULL, result jsonb NOT NULL, planner_decision text, data_mode text NOT NULL);
