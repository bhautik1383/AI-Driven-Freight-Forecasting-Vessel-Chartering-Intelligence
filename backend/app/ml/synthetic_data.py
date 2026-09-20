"""
Generates a plausible daily freight-rate history for each
(commodity, route, vessel_type) combination so the models below have
something to train and predict on out of the box.

THIS IS DEMO DATA. Replace `load_history()` with a query against
FreightRateHistory rows populated by app/connectors/baltic_exchange_connector.py
once you have a real feed — everything downstream (training, forecasting,
SHAP) is written against a plain pandas DataFrame and does not care where
the rows came from.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

BASE_RATES = {
    "aus_ec":  {"coking_coal": 19.2, "limestone": 12.4, "other_bulk": 14.8},
    "indo_ec": {"coking_coal": 11.8, "limestone": 8.6,  "other_bulk": 10.1},
    "saf_ec":  {"coking_coal": 16.6, "limestone": 11.9, "other_bulk": 13.5},
    "us_ec":   {"coking_coal": 24.7, "limestone": 16.2, "other_bulk": 18.9},
}
VESSEL_FACTOR = {"capesize": 1.0, "panamax": 1.12, "supramax": 1.24}


def generate_history(commodity: str, route: str, vessel_type: str, days: int = 400, seed: int | None = None) -> pd.DataFrame:
    base = BASE_RATES.get(route, BASE_RATES["aus_ec"]).get(commodity, 15.0) * VESSEL_FACTOR.get(vessel_type, 1.0)
    rng = np.random.default_rng(seed or (hash((commodity, route, vessel_type)) % (2**32)))

    dates = [datetime.utcnow().date() - timedelta(days=days - i) for i in range(days)]
    level = base * 1.1
    values = []
    for i in range(days):
        seasonal = 0.05 * base * np.sin(2 * np.pi * i / 90)         # quarterly demand cycle
        shock = rng.normal(0, 0.02 * base)                           # daily volatility
        drift = -0.0006 * base * (i / days)                          # gentle multi-month softening
        level = max(base * 0.55, level + shock + drift * 0 + seasonal * 0.02)
        level += drift
        values.append(round(level, 3))

    df = pd.DataFrame({"ds": dates, "y": values})
    df["commodity"] = commodity
    df["route"] = route
    df["vessel_type"] = vessel_type

    # Engineered features gradient-boosted models actually use
    df["lag_1"] = df["y"].shift(1)
    df["lag_7"] = df["y"].shift(7)
    df["lag_30"] = df["y"].shift(30)
    df["roll_mean_7"] = df["y"].rolling(7).mean()
    df["roll_std_7"] = df["y"].rolling(7).std()
    df["day_of_year"] = pd.to_datetime(df["ds"]).dt.dayofyear
    df["congestion_index"] = 0.5 + 0.5 * np.sin(2 * np.pi * df["day_of_year"] / 60) + rng.normal(0, 0.05, days)
    df["fx_usd_inr_index"] = 100 + np.cumsum(rng.normal(0, 0.15, days))
    df = df.dropna().reset_index(drop=True)
    return df
