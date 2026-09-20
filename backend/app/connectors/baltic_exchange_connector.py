"""
Baltic Exchange freight index connector.

Baltic Exchange indices (BDI, BCI, BPI, BSI) are a paid subscription, not a
public API — you'll get a data-feed spec and credentials once you sign up
at https://www.balticexchange.com/. This stub shows where that call goes;
until BALTIC_EXCHANGE_API_KEY is set, callers should keep using
app/ml/synthetic_data.py for historical rates.
"""
import httpx
from app.config import settings


async def get_index(index_code: str = "BDI") -> dict | None:
    if not settings.live_baltic_enabled:
        return None
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.baltic_exchange_base_url}/indices/{index_code}",
            headers={"Authorization": f"Bearer {settings.baltic_exchange_api_key}"},
        )
        resp.raise_for_status()
        return resp.json()
