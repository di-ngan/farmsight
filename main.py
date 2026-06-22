"""
FarmSight — Crop Health Diagnosis CLI
Usage:
    uv run python main.py --demo
    uv run python main.py --lat 10.7867 --lon 76.6548 --question "Why are my paddy leaves turning yellow?"
    uv run python main.py --geojson my_field.geojson --question "How is my crop doing?"
    uv run python main.py --lat 10.7867 --lon 76.6548 --buffer-m 200 --question "Crop status?"
"""

import argparse
import asyncio
import json
import pathlib
import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from agents.runner import run_diagnosis, DEMO_LAT, DEMO_LON, DEMO_QUESTION


def validate_geojson(path: pathlib.Path) -> str:
    text = path.read_text()
    try:
        gj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

    allowed = ("Polygon", "MultiPolygon", "Feature", "FeatureCollection")
    if gj.get("type") not in allowed:
        raise ValueError(
            f"Unsupported GeoJSON type '{gj.get('type')}'. Must be one of: {', '.join(allowed)}"
        )

    # rough bounding-box size warning (~0.09° ≈ 10km)
    coords = _extract_coords(gj)
    if coords:
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        span = max(max(lons) - min(lons), max(lats) - min(lats))
        if span > 0.09:
            print(f"  Warning: GeoJSON spans ~{span*111:.0f}km — larger than a typical paddy field. Confirm this is correct.")

    return text


def _extract_coords(gj: dict) -> list:
    t = gj.get("type", "")
    if t == "Polygon":
        return [c for ring in gj["coordinates"] for c in ring]
    if t == "MultiPolygon":
        return [c for poly in gj["coordinates"] for ring in poly for c in ring]
    if t == "Feature":
        return _extract_coords(gj.get("geometry") or {})
    if t == "FeatureCollection":
        coords = []
        for feat in gj.get("features", []):
            coords.extend(_extract_coords(feat))
        return coords
    return []


def print_report(state: dict, lat: float | None, lon: float | None, geojson_path: pathlib.Path | None, buffer_m: int):
    ndvi = state.get("ndvi_result")
    rain = state.get("rainfall_result")
    diagnosis = state.get("diagnosis", "No diagnosis produced.")
    season = state.get("season", "unknown")
    das = state.get("days_after_sowing", "unknown")

    if isinstance(ndvi, str):
        try:
            ndvi = json.loads(ndvi)
        except Exception:
            ndvi = {}
    if isinstance(rain, str):
        try:
            rain = json.loads(rain)
        except Exception:
            rain = {}

    ndvi = ndvi or {}
    rain = rain or {}

    geom_label = f"GeoJSON: {geojson_path.name}" if geojson_path else f"point {lat}°N {lon}°E  (buffer {buffer_m}m)"

    print()
    print("═" * 60)
    print("  FarmSight — Crop Health Report")
    print(f"  Date   : {datetime.date.today()}")
    print(f"  Field  : {geom_label}")
    print(f"  Season : {season}  |  ~{das} days after sowing")
    print("═" * 60)

    print()
    print("  SATELLITE DATA (Sentinel-2 NDVI)")
    if ndvi.get("warning"):
        print(f"  ⚠  {ndvi['warning']}")
    latest = ndvi.get("latest_image_date", "N/A")
    recency = ndvi.get("data_recency_days", "N/A")
    print(f"  Latest image : {latest}  ({recency} days ago)")
    for pt in ndvi.get("ndvi_series", []):
        print(f"    {pt['date']}  NDVI={pt['ndvi_mean']:.3f}  cloud={pt['cloud_pct']}%")

    print()
    print("  RAINFALL (last 30 days — Open-Meteo)")
    total = rain.get("total_mm_30d", "N/A")
    anomaly = (rain.get("anomaly_indicator") or "unknown").upper()
    print(f"  Total: {total} mm  |  Status: {anomaly}")
    if rain.get("warning"):
        print(f"  ⚠  {rain['warning']}")

    print()
    print("  DIAGNOSIS & RECOMMENDATION")
    print("  " + "-" * 56)
    for line in diagnosis.splitlines():
        print(f"  {line}")

    print()
    print("═" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="FarmSight — AI crop health diagnosis")
    parser.add_argument("--lat", type=float, help="Field latitude")
    parser.add_argument("--lon", type=float, help="Field longitude")
    parser.add_argument("--buffer-m", type=int, default=100, dest="buffer_m",
                        help="Buffer radius in metres around lat/lon (default 100)")
    parser.add_argument("--question", type=str, default="What is the crop health status?",
                        help="Your question about the crop")
    parser.add_argument("--geojson", type=pathlib.Path,
                        help="Path to GeoJSON file defining exact field boundary")
    parser.add_argument("--demo", action="store_true",
                        help="Run with demo Palakkad paddy coordinates")
    args = parser.parse_args()

    if args.demo:
        lat, lon = DEMO_LAT, DEMO_LON
        geojson_str = None
        geojson_path = None
        if args.question == "What is the crop health status?":
            args.question = DEMO_QUESTION
    elif args.geojson:
        try:
            geojson_str = validate_geojson(args.geojson)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        lat, lon = None, None
        geojson_path = args.geojson
    elif args.lat is not None and args.lon is not None:
        if not (-90 <= args.lat <= 90):
            print(f"Error: latitude must be between -90 and 90, got {args.lat}")
            sys.exit(1)
        if not (-180 <= args.lon <= 180):
            print(f"Error: longitude must be between -180 and 180, got {args.lon}")
            sys.exit(1)
        lat, lon = args.lat, args.lon
        geojson_str = None
        geojson_path = None
    else:
        parser.print_help()
        sys.exit(1)

    geojson_path = args.geojson if args.geojson else None

    state = asyncio.run(run_diagnosis(lat, lon, args.question, geojson_str))
    print_report(state, lat, lon, geojson_path, args.buffer_m)


if __name__ == "__main__":
    main()
