import hashlib
import json
import os
import datetime
from pathlib import Path


class FileCache:
    def __init__(self, cache_dir: str = "dev_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        path = self._key_to_path(key)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return None

    def set(self, key: str, data: dict) -> None:
        path = self._key_to_path(key)
        with open(path, "w") as f:
            json.dump(data, f)


def make_cache_key(
    lat: float | None,
    lon: float | None,
    buffer_m: int,
    lookback_days: int,
    geojson_str: str | None = None,
) -> str:
    today = datetime.date.today().isoformat()
    if geojson_str:
        raw = f"geojson_{hashlib.sha256(geojson_str.encode()).hexdigest()}_{lookback_days}_{today}"
    else:
        raw = f"{lat}_{lon}_{buffer_m}_{lookback_days}_{today}"
    return hashlib.sha256(raw.encode()).hexdigest()


def make_snapshot_key(
    lat: float | None,
    lon: float | None,
    buffer_m: int,
    geojson_str: str | None = None,
) -> str:
    today = datetime.date.today().isoformat()
    if geojson_str:
        raw = f"snapshot_geojson_{hashlib.sha256(geojson_str.encode()).hexdigest()}_{today}"
    else:
        raw = f"snapshot_{lat}_{lon}_{buffer_m}_{today}"
    return hashlib.sha256(raw.encode()).hexdigest()
