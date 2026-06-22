from mcp_servers.sentinel_mcp.cache import FileCache, make_cache_key, make_snapshot_key
from mcp_servers.sentinel_mcp import gee_client

_cache = FileCache()
_gee_initialized = False


def _ensure_gee():
    global _gee_initialized
    if not _gee_initialized:
        gee_client.init_gee()
        _gee_initialized = True


def _validate_coords(lat: float | None, lon: float | None, geojson_str: str | None) -> None:
    if geojson_str:
        return  # geometry comes from GeoJSON; lat/lon not required
    if lat is None or lon is None:
        raise ValueError("latitude and longitude are required when geojson is not provided")
    if not (-90 <= lat <= 90):
        raise ValueError(f"latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"longitude must be between -180 and 180, got {lon}")


def run_get_ndvi_trend(arguments: dict) -> dict:
    lat = float(arguments["latitude"]) if arguments.get("latitude") is not None else None
    lon = float(arguments["longitude"]) if arguments.get("longitude") is not None else None
    buffer_m = int(arguments.get("buffer_meters", 100))
    lookback_days = int(arguments.get("lookback_days", 60))
    max_cloud_pct = int(arguments.get("max_cloud_pct", 20))
    geojson_str = arguments.get("geojson") or None

    _validate_coords(lat, lon, geojson_str)
    _ensure_gee()

    cache_key = make_cache_key(lat, lon, buffer_m, lookback_days, geojson_str)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    result = gee_client.get_ndvi_series(
        lat=lat,
        lon=lon,
        buffer_m=buffer_m,
        lookback_days=lookback_days,
        max_cloud_pct=max_cloud_pct,
        geojson_str=geojson_str,
    )

    _cache.set(cache_key, result)
    return result


def run_get_field_snapshot(arguments: dict) -> dict:
    lat = float(arguments["latitude"]) if arguments.get("latitude") is not None else None
    lon = float(arguments["longitude"]) if arguments.get("longitude") is not None else None
    buffer_m = int(arguments.get("buffer_meters", 100))
    max_cloud_pct = int(arguments.get("max_cloud_pct", 20))
    geojson_str = arguments.get("geojson") or None

    _validate_coords(lat, lon, geojson_str)
    _ensure_gee()

    cache_key = make_snapshot_key(lat, lon, buffer_m, geojson_str)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    result = gee_client.get_single_snapshot(
        lat=lat,
        lon=lon,
        buffer_m=buffer_m,
        max_cloud_pct=max_cloud_pct,
        geojson_str=geojson_str,
    )

    _cache.set(cache_key, result)
    return result
