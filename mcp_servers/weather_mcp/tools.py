import hashlib
import json
import datetime
from pathlib import Path

from mcp_servers.weather_mcp import openmeteo_client

_cache_dir = Path("dev_cache")


def _cache_key(lat: float, lon: float, lookback_days: int) -> str:
    today = datetime.date.today().isoformat()
    raw = f"weather_{lat}_{lon}_{lookback_days}_{today}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> dict | None:
    path = _cache_dir / f"{key}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _cache_set(key: str, data: dict) -> None:
    _cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_dir / f"{key}.json"
    with open(path, "w") as f:
        json.dump(data, f)


def _validate_coords(lat: float, lon: float) -> None:
    if not (-90 <= lat <= 90):
        raise ValueError(f"latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"longitude must be between -180 and 180, got {lon}")


async def run_get_rainfall_trend(arguments: dict) -> dict:
    lat = float(arguments["latitude"])
    lon = float(arguments["longitude"])
    lookback_days = int(arguments.get("lookback_days", 60))

    _validate_coords(lat, lon)

    key = _cache_key(lat, lon, lookback_days)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    result = await openmeteo_client.get_rainfall(lat, lon, lookback_days)
    _cache_set(key, result)
    return result
