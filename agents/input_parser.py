import datetime

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

from agents.coordinator import get_season, days_after_sowing


def set_field_inputs(
    latitude: float,
    longitude: float,
    question: str,
    tool_context: ToolContext,
) -> dict:
    """Parse and store field coordinates and the farmer's question in session state."""
    today = datetime.date.today()
    season = get_season(today)
    das = days_after_sowing(season, today)

    tool_context.state["input_lat"] = latitude
    tool_context.state["input_lon"] = longitude
    tool_context.state["input_question"] = question
    tool_context.state["input_geojson"] = None
    tool_context.state["season"] = season
    tool_context.state["sowing_date"] = (
        f"{today.year}-06-01" if season == "kharif" else f"{today.year}-11-01"
    )
    tool_context.state["days_after_sowing"] = das

    return {"status": "ok", "latitude": latitude, "longitude": longitude, "season": season}


input_parser_agent = LlmAgent(
    name="input_parser_agent",
    model="gemini-3.5-flash",
    instruction=(
        "You are the FarmSight input parser. "
        "Your only job is to extract the field coordinates and the crop question from the user's message, "
        "then call set_field_inputs with those values. "
        "If the user gives a place name instead of coordinates (e.g. 'Palakkad, Kerala'), "
        "use your knowledge to infer approximate decimal coordinates. "
        "After calling the tool, reply only with: 'Inputs captured. Starting diagnosis...'"
    ),
    tools=[set_field_inputs],
    include_contents="none",
)
