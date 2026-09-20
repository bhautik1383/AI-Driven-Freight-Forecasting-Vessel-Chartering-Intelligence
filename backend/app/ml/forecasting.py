"""
Freight-rate forecasting.

- XGBoost / CatBoost: trained on lag + rolling + seasonal + congestion + fx
  features, forecast recursively (each predicted day feeds the next day's lags).
- ARIMA: statsmodels, trend/seasonality baseline as described in the PPT.
- Prophet: optional — only used if the `prophet` package is installed
  (it has a heavier native build dependency, so it's not required).

All three return the same shape so the API layer doesn't care which was used.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from app.ml.synthetic_data import generate_history

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from catboost import CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

FEATURE_COLS = ["lag_1", "lag_7", "lag_30", "roll_mean_7", "roll_std_7",
                "day_of_year", "congestion_index", "fx_usd_inr_index"]


def _fit_tree_model(df: pd.DataFrame, model_name: str):
    X, y = df[FEATURE_COLS], df["y"]
    if model_name == "catboost" and HAS_CATBOOST:
        model = CatBoostRegressor(iterations=200, depth=4, learning_rate=0.08, verbose=False)
        model.fit(X, y)
        return model
    if HAS_XGB:
        model = xgb.XGBRegressor(n_estimators=250, max_depth=4, learning_rate=0.06,
                                  subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror")
        model.fit(X, y)
        return model
    return None  # falls back to naive drift below


def _recursive_forecast(df: pd.DataFrame, model, horizon: int) -> list[float]:
    history = df.copy().reset_index(drop=True)
    preds = []
    for step in range(horizon):
        last = history.iloc[-1]
        day_of_year = (last["day_of_year"] + 1) % 365 or 365
        feat = pd.DataFrame([{
            "lag_1": history["y"].iloc[-1],
            "lag_7": history["y"].iloc[-7] if len(history) >= 7 else history["y"].mean(),
            "lag_30": history["y"].iloc[-30] if len(history) >= 30 else history["y"].mean(),
            "roll_mean_7": history["y"].tail(7).mean(),
            "roll_std_7": history["y"].tail(7).std() or 0.1,
            "day_of_year": day_of_year,
            "congestion_index": last["congestion_index"],
            "fx_usd_inr_index": last["fx_usd_inr_index"],
        }])
        pred = float(model.predict(feat)[0])
        preds.append(pred)
        new_row = last.copy()
        new_row["y"] = pred
        new_row["day_of_year"] = day_of_year
        history = pd.concat([history, pd.DataFrame([new_row])], ignore_index=True)
    return preds


def _arima_forecast(df: pd.DataFrame, horizon: int) -> list[float]:
    if not HAS_ARIMA:
        # naive drift fallback
        drift = (df["y"].iloc[-1] - df["y"].iloc[-30]) / 30 if len(df) >= 30 else 0
        return [float(df["y"].iloc[-1] + drift * i) for i in range(1, horizon + 1)]
    model = ARIMA(df["y"], order=(2, 1, 2)).fit()
    fc = model.forecast(steps=horizon)
    return [float(v) for v in fc]


def _prophet_forecast(df: pd.DataFrame, horizon: int) -> list[float]:
    m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    m.fit(df[["ds", "y"]])
    future = m.make_future_dataframe(periods=horizon)
    fc = m.predict(future)
    return fc["yhat"].tail(horizon).tolist()


def run_forecast(commodity: str, route: str, vessel_type: str, horizon: int, model_name: str) -> dict:
    df = generate_history(commodity, route, vessel_type, days=400)
    current = float(df["y"].iloc[-1])

    if model_name == "arima":
        point_forecast = _arima_forecast(df, horizon)
    elif model_name == "prophet" and HAS_PROPHET:
        point_forecast = _prophet_forecast(df, horizon)
    else:
        model = _fit_tree_model(df, model_name)
        if model is None:
            drift = (df["y"].iloc[-1] - df["y"].iloc[-30]) / 30
            point_forecast = [float(current + drift * i) for i in range(1, horizon + 1)]
        else:
            point_forecast = _recursive_forecast(df, model, horizon)

    resid_std = float(df["y"].diff().std() or 0.3)
    upper, lower = [], []
    for i, v in enumerate(point_forecast, start=1):
        band = resid_std * np.sqrt(i) * 1.28   # ~80% interval
        upper.append(v + band)
        lower.append(v - band)

    expected = point_forecast[-1]
    pct_change = ((expected - current) / current) * 100
    confidence = max(0.55, 0.92 - (horizon / 250) - (0.05 if model_name == "arima" else 0))

    hist_tail = df.tail(30)
    return {
        "labels_hist": [d.strftime("%Y-%m-%d") for d in pd.to_datetime(hist_tail["ds"])],
        "historical": hist_tail["y"].round(2).tolist(),
        "forecast": [round(v, 2) for v in point_forecast],
        "forecast_upper": [round(v, 2) for v in upper],
        "forecast_lower": [round(v, 2) for v in lower],
        "current_rate": round(current, 2),
        "expected_rate": round(expected, 2),
        "pct_change": round(pct_change, 2),
        "confidence": round(confidence, 3),
        "model_used": model_name,
        "training_df": df,   # kept for SHAP explainability, not serialized to API
    }
