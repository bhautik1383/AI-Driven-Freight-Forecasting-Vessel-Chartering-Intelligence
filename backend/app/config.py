"""Small environment adapter shared by optional production connectors.

The demo API does not require any secrets. Connector modules read this object
only when a deployment enables a paid or government data source.
"""
import os

class Settings:
    ais_api_key = os.getenv("AIS_API_KEY", "")
    baltic_exchange_api_key = os.getenv("BALTIC_EXCHANGE_API_KEY", "")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    ais_provider = os.getenv("AIS_PROVIDER", "")
    ais_api_base_url = os.getenv("AIS_API_BASE_URL", "")
    agent_model = os.getenv("AGENT_MODEL", "claude-sonnet-4-20250514")
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    live_ais_enabled = bool(ais_api_key and ais_provider and ais_api_base_url)
    live_baltic_enabled = bool(baltic_exchange_api_key)

settings = Settings()
