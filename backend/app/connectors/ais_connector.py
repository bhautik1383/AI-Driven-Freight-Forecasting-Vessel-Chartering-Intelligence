"""
Vessel-position connector.

get_vessels() returns demo vessels until AIS_PROVIDER + AIS_API_KEY are set
in .env, at which point it calls the real provider instead. Swap in the
correct request shape for whichever vendor you sign with — the three
biggest are sketched below as a starting point; check current docs before
wiring a contract, endpoint paths and payloads change over time.
"""
import httpx
from app.config import settings

DEMO_VESSELS = [
    {"id": "v1", "name": "MV Coral Horizon", "vessel_type": "Capesize", "draft_m": 17.2, "cargo": "Coking Coal",
     "origin": "Australia", "destination_port_id": "dhamra", "eta": "2026-09-14", "status": "ontime",
     "lat": 14.2, "lng": 88.4, "delay_risk": "Low"},
    {"id": "v2", "name": "MV Deccan Trader", "vessel_type": "Capesize", "draft_m": 15.6, "cargo": "Coking Coal",
     "origin": "Indonesia", "destination_port_id": "paradip", "eta": "2026-09-11", "status": "delayed",
     "lat": 9.1, "lng": 95.6, "delay_risk": "Medium"},
    {"id": "v3", "name": "MV Steel Vanguard", "vessel_type": "Panamax", "draft_m": 18.9, "cargo": "Limestone",
     "origin": "South Africa", "destination_port_id": "gangavaram", "eta": "2026-09-19", "status": "transit",
     "lat": -6.4, "lng": 60.2, "delay_risk": "Low"},
    {"id": "v4", "name": "MV Northern Ridge", "vessel_type": "Capesize", "draft_m": 18.4, "cargo": "Coking Coal",
     "origin": "Australia", "destination_port_id": "paradip", "eta": "2026-09-16", "status": "risk",
     "lat": 5.8, "lng": 101.1, "delay_risk": "High"},
]


async def get_vessels() -> tuple[list[dict], str]:
    """Returns (vessels, source) where source is 'demo' or 'live'."""
    if not settings.live_ais_enabled:
        return DEMO_VESSELS, "demo"

    async with httpx.AsyncClient(timeout=15) as client:
        if settings.ais_provider == "marinetraffic":
            # https://www.marinetraffic.com/en/ais-api-services  (endpoint/params vary by plan)
            resp = await client.get(
                f"{settings.ais_api_base_url}/exportvessels/v:8",
                params={"key": settings.ais_api_key, "protocol": "jsono"},
            )
        elif settings.ais_provider == "kpler":
            # https://www.kpler.com — GraphQL/REST endpoints, auth via bearer token
            resp = await client.get(
                f"{settings.ais_api_base_url}/vessels",
                headers={"Authorization": f"Bearer {settings.ais_api_key}"},
            )
        elif settings.ais_provider == "spire":
            # https://spire.com/maritime/ — REST + gRPC options
            resp = await client.get(
                f"{settings.ais_api_base_url}/vessels/positions",
                headers={"authorization": settings.ais_api_key},
            )
        else:
            return DEMO_VESSELS, "demo"

        resp.raise_for_status()
        raw = resp.json()
        # NOTE: map `raw` into the same shape as DEMO_VESSELS here — the exact
        # field names depend on the provider's response schema.
        return raw, "live"
