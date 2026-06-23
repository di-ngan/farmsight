import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.runner import run_diagnosis


class DiagnoseRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Field latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Field longitude")
    question: str = Field(
        default="What is the crop health status?",
        description="Farmer's question about the crop",
    )
    geojson: str | None = Field(
        default=None,
        description="Optional GeoJSON string (Polygon/Feature/FeatureCollection) for exact field boundary",
    )


class DiagnoseResponse(BaseModel):
    diagnosis: str
    season: str
    days_after_sowing: int
    ndvi_result: dict[str, Any] | None = None
    rainfall_result: dict[str, Any] | None = None


app = FastAPI(
    title="FarmSight API",
    description="Crop health diagnosis using Sentinel-2 NDVI and Open-Meteo rainfall data.",
    version="0.1.0",
)

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest) -> DiagnoseResponse:
    try:
        state = await run_diagnosis(req.latitude, req.longitude, req.question, req.geojson)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    def _parse(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {}
        return value or {}

    return DiagnoseResponse(
        diagnosis=state.get("diagnosis", "No diagnosis produced."),
        season=state.get("season", "unknown"),
        days_after_sowing=state.get("days_after_sowing", 0),
        ndvi_result=_parse(state.get("ndvi_result")),
        rainfall_result=_parse(state.get("rainfall_result")),
    )
