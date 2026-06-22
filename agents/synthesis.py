import json
from pathlib import Path

from google.adk.agents import LlmAgent

_SKILL_DIR = Path(__file__).parent.parent / "skills" / "crop-diagnosis"
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_skill_content() -> str:
    skill_md = (_SKILL_DIR / "SKILL.md").read_text()
    ndvi_norms = (_SKILL_DIR / "references" / "ndvi_norms.md").read_text()
    output_template = (_SKILL_DIR / "assets" / "output_template.md").read_text()
    return f"{skill_md}\n\n---\n\n{ndvi_norms}\n\n---\n\n{output_template}"


def _load_crop_profile() -> str:
    return json.dumps(json.loads((_DATA_DIR / "crop_profile.json").read_text()), indent=2)


def _instruction(ctx) -> str:
    ndvi_result = ctx.state.get("ndvi_result", "NOT AVAILABLE")
    rainfall_result = ctx.state.get("rainfall_result", "NOT AVAILABLE")
    season = ctx.state.get("season", "unknown")
    question = ctx.state.get("input_question", "Diagnose crop health")
    lat = ctx.state.get("input_lat", "unknown")
    lon = ctx.state.get("input_lon", "unknown")
    days_after_sowing = ctx.state.get("days_after_sowing", "unknown")

    # determine how to refer to the field geometry in the report
    try:
        ndvi_data = json.loads(ndvi_result) if isinstance(ndvi_result, str) else ndvi_result
        geom_source = ndvi_data.get("geometry_source", "point_buffer")
    except Exception:
        geom_source = "point_buffer"

    geom_label = "your uploaded field boundary" if geom_source == "geojson_upload" else f"a {100}m buffer around the provided coordinates"

    skill_content = _load_skill_content()
    crop_profile = _load_crop_profile()

    return f"""You are the Synthesis Agent for FarmSight. Produce a structured crop health diagnosis.

## Farmer's Question
{question}

## Location
Latitude: {lat}, Longitude: {lon}
Season: {season}
Estimated days after sowing: {days_after_sowing}
Field geometry: {geom_label}

## Satellite Data (NDVI)
{ndvi_result}

## Weather Data (Rainfall)
{rainfall_result}

## Crop Profile
{crop_profile}

## Diagnosis Skill — Follow These Instructions Exactly
{skill_content}

Produce the diagnosis now. Use the output template format. Be specific — cite the actual NDVI values and rainfall numbers. When referencing the field location, use "{geom_label}"."""


synthesis_agent = LlmAgent(
    name="synthesis_agent",
    model="gemini-3.5-flash",
    instruction=_instruction,
    output_key="diagnosis",
    include_contents="none",
)
