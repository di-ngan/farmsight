"""
FarmSight agent runner.
Usage:
    uv run python agents/runner.py --demo
    uv run python agents/runner.py --lat 10.7867 --lon 76.6548 --question "Why is my paddy showing yellow leaves?"
    uv run python agents/runner.py --geojson my_field.geojson --question "How is my crop doing?"
"""

import argparse
import asyncio
import pathlib
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from agents.coordinator import coordinator, get_season, days_after_sowing

DEMO_LAT = 10.7867
DEMO_LON = 76.6548
DEMO_QUESTION = "My paddy is showing yellow leaves and the growth looks stunted. What is causing this and what should I do?"


async def run_diagnosis(
    lat: float | None,
    lon: float | None,
    question: str,
    geojson_str: str | None = None,
) -> dict:
    import datetime
    today = datetime.date.today()
    season = get_season(today)
    das = days_after_sowing(season, today)

    runner = InMemoryRunner(agent=coordinator, app_name="farmsight")

    session = await runner.session_service.create_session(
        app_name="farmsight",
        user_id="farmer",
        state={
            "input_lat": lat,
            "input_lon": lon,
            "input_question": question,
            "input_geojson": geojson_str,
            "season": season,
            "sowing_date": f"{today.year}-06-01" if season == "kharif" else f"{today.year}-11-01",
            "days_after_sowing": das,
        },
    )

    print(f"Session: {session.id}")
    print(f"Season: {season} | Days after sowing: {das}")
    print(f"Geometry: {'GeoJSON upload' if geojson_str else f'point buffer ({lat}, {lon})'}")
    print("Running: Remote Sensing → Weather → Synthesis\n")

    async for event in runner.run_async(
        user_id="farmer",
        session_id=session.id,
        new_message=genai_types.Content(
            parts=[genai_types.Part(text=question)],
            role="user",
        ),
    ):
        if hasattr(event, "author") and event.author:
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        preview = part.text[:80].replace("\n", " ")
                        print(f"  [{event.author}] {preview}...")

    final_session = await runner.session_service.get_session(
        app_name="farmsight",
        user_id="farmer",
        session_id=session.id,
    )

    return dict(final_session.state)


def main():
    parser = argparse.ArgumentParser(description="FarmSight crop health diagnosis")
    parser.add_argument("--lat", type=float, help="Field latitude")
    parser.add_argument("--lon", type=float, help="Field longitude")
    parser.add_argument("--question", type=str, default="What is the crop health status?")
    parser.add_argument("--geojson", type=pathlib.Path, help="Path to GeoJSON field boundary file")
    parser.add_argument("--demo", action="store_true", help="Run with demo Palakkad coordinates")
    args = parser.parse_args()

    if args.demo:
        lat, lon = DEMO_LAT, DEMO_LON
        if args.question == "What is the crop health status?":
            args.question = DEMO_QUESTION
    elif args.geojson:
        lat, lon = None, None
    elif args.lat and args.lon:
        lat, lon = args.lat, args.lon
    else:
        parser.print_help()
        sys.exit(1)

    geojson_str = args.geojson.read_text() if args.geojson else None
    state = asyncio.run(run_diagnosis(lat, lon, args.question, geojson_str))

    print("\n" + "=" * 60)
    print("FARMSIGHT DIAGNOSIS")
    print("=" * 60)
    print(state.get("diagnosis", "No diagnosis produced."))


if __name__ == "__main__":
    main()
