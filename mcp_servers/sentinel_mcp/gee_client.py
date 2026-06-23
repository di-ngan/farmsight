import json
import os
import datetime
from dotenv import load_dotenv
import ee

load_dotenv()


def init_gee() -> None:
    key_path = os.environ.get("GEE_SERVICE_ACCOUNT_KEY_PATH")
    email = os.environ.get("GEE_SERVICE_ACCOUNT_EMAIL")
    if not key_path or not email:
        raise RuntimeError(
            "GEE_SERVICE_ACCOUNT_KEY_PATH and GEE_SERVICE_ACCOUNT_EMAIL must be set"
        )
    credentials = ee.ServiceAccountCredentials(email, key_path)
    ee.Initialize(credentials)


def parse_geometry(
    lat: float | None = None,
    lon: float | None = None,
    buffer_m: int = 100,
    geojson_str: str | None = None,
) -> ee.Geometry:
    if geojson_str:
        gj = json.loads(geojson_str)
        if gj["type"] == "FeatureCollection":
            return ee.FeatureCollection(gj).geometry()
        elif gj["type"] == "Feature":
            return ee.Geometry(gj["geometry"])
        else:
            return ee.Geometry(gj)
    return ee.Geometry.Point([lon, lat]).buffer(buffer_m).bounds()


def _build_ndvi_collection(
    aoi: ee.Geometry,
    start: str,
    end: str,
    max_cloud_pct: int,
):
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
    )

    def annotate(image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("ndvi")
        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean()
                .combine(ee.Reducer.min(), sharedInputs=True)
                .combine(ee.Reducer.max(), sharedInputs=True),
            geometry=aoi,
            scale=10,
            maxPixels=1e9,
        )
        return ee.Feature(None, {
            "date": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd"),
            "ndvi_mean": stats.get("ndvi_mean"),
            "ndvi_min": stats.get("ndvi_min"),
            "ndvi_max": stats.get("ndvi_max"),
            "cloud_pct": image.get("CLOUDY_PIXEL_PERCENTAGE"),
        })

    return collection.map(annotate)


def get_ndvi_series(
    lat: float | None = None,
    lon: float | None = None,
    buffer_m: int = 100,
    lookback_days: int = 60,
    max_cloud_pct: int = 20,
    geojson_str: str | None = None,
) -> dict:
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=lookback_days)).isoformat()
    end = today.isoformat()

    aoi = parse_geometry(lat, lon, buffer_m, geojson_str)
    geometry_source = "geojson_upload" if geojson_str else "point_buffer"

    fc = _build_ndvi_collection(aoi, start, end, max_cloud_pct)
    # Fetch up to 200 images directly; avoids a separate size().getInfo() round-trip
    features = fc.toList(200).getInfo()

    if not features:
        return {
            "ndvi_series": [],
            "latest_image_date": None,
            "data_recency_days": None,
            "geometry_source": geometry_source,
            "warning": f"No cloud-free imagery found in {lookback_days}-day window (max cloud {max_cloud_pct}%)",
        }

    series = []
    for feat in features:
        props = feat["properties"]
        ndvi_mean = props.get("ndvi_mean")
        if ndvi_mean is None:
            continue
        series.append({
            "date": props["date"],
            "ndvi_mean": round(float(ndvi_mean), 4),
            "cloud_pct": round(float(props.get("cloud_pct", 0) or 0), 1),
        })

    series.sort(key=lambda x: x["date"])

    latest_date = series[-1]["date"] if series else None
    recency_days = None
    if latest_date:
        recency_days = (today - datetime.date.fromisoformat(latest_date)).days

    return {
        "ndvi_series": series,
        "latest_image_date": latest_date,
        "data_recency_days": recency_days,
        "geometry_source": geometry_source,
        "warning": None,
    }


def get_single_snapshot(
    lat: float | None = None,
    lon: float | None = None,
    buffer_m: int = 100,
    max_cloud_pct: int = 20,
    geojson_str: str | None = None,
) -> dict:
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=60)).isoformat()
    end = today.isoformat()

    aoi = parse_geometry(lat, lon, buffer_m, geojson_str)
    geometry_source = "geojson_upload" if geojson_str else "point_buffer"

    fc = _build_ndvi_collection(aoi, start, end, max_cloud_pct)
    features = fc.toList(200).getInfo()

    if not features:
        return {
            "date": None,
            "ndvi_mean": None,
            "ndvi_min": None,
            "ndvi_max": None,
            "geometry_source": geometry_source,
            "warning": f"No cloud-free imagery found in 60-day window (max cloud {max_cloud_pct}%)",
        }

    features.sort(key=lambda f: f["properties"]["date"], reverse=True)
    props = features[0]["properties"]

    return {
        "date": props["date"],
        "ndvi_mean": round(float(props.get("ndvi_mean") or 0), 4),
        "ndvi_min": round(float(props.get("ndvi_min") or 0), 4),
        "ndvi_max": round(float(props.get("ndvi_max") or 0), 4),
        "geometry_source": geometry_source,
        "warning": None,
    }
