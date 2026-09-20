"""
DGCIS (Directorate General of Commercial Intelligence & Statistics) and
Indian Ports Association data are typically published as periodic
CSV/Excel reports rather than a live REST API. The realistic integration
pattern is: download the latest report, drop it at DGCIS_DATA_PATH /
IPA_DATA_PATH, and load it here on a schedule (e.g. monthly) rather than
per-request.
"""
import os
import pandas as pd
from app.config import settings


def load_dgcis_trade_data() -> pd.DataFrame | None:
    if not settings.dgcis_data_path or not os.path.exists(settings.dgcis_data_path):
        return None
    return pd.read_csv(settings.dgcis_data_path)


def load_ipa_traffic_data() -> pd.DataFrame | None:
    if not settings.ipa_data_path or not os.path.exists(settings.ipa_data_path):
        return None
    return pd.read_csv(settings.ipa_data_path)
