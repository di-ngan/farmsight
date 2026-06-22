import httpx
from datetime import date, timedelta

_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Rough 30-day normal rainfall (mm) for Kerala by month
_KERALA_MONTHLY_NORMAL_MM = {
    1: 20, 2: 20, 3: 30, 4: 50, 5: 150,
    6: 300, 7: 350, 8: 280, 9: 200, 10: 120,
    11: 60, 12: 20,
}


async def get_rainfall(lat: float, lon: float, lookback_days: int = 60) -> dict:
    end = date.today()
    start = end - timedelta(days=lookback_days)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(_ARCHIVE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

    series = [
        {"date": d, "rainfall_mm": round(float(p), 1)}
        for d, p in zip(data["daily"]["time"], data["daily"]["precipitation_sum"])
        if p is not None
    ]

    total_30d = sum(s["rainfall_mm"] for s in series[-30:])
    anomaly = _anomaly_flag(total_30d, start.month)

    return {
        "rainfall_series": series,
        "total_mm_30d": round(total_30d, 1),
        "anomaly_indicator": anomaly,
        "warning": None,
    }


def _anomaly_flag(total_mm: float, month: int) -> str:
    normal = _KERALA_MONTHLY_NORMAL_MM.get(month, 100)
    ratio = total_mm / normal if normal else 1.0
    if ratio < 0.5:
        return "drought"
    if ratio > 1.8:
        return "excess"
    return "normal"
