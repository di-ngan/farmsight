import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters

_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "sentinel_mcp", "server.py")
)


def _instruction(ctx) -> str:
    lat = ctx.state.get("input_lat")
    lon = ctx.state.get("input_lon")
    geojson = ctx.state.get("input_geojson")

    if geojson:
        return (
            "You are the Remote Sensing Agent for FarmSight. "
            "Call the get_ndvi_trend tool with the geojson field boundary provided in session state. "
            f"Pass the geojson argument as-is: {geojson[:200]}... "
            "Do not pass latitude or longitude — the geojson defines the field. "
            "Return ONLY the raw JSON result from the tool — no extra commentary."
        )
    return (
        "You are the Remote Sensing Agent for FarmSight. "
        f"Call the get_ndvi_trend tool with latitude={lat}, longitude={lon}, "
        "lookback_days=60, max_cloud_pct=20. "
        "Return ONLY the raw JSON result from the tool — no extra commentary."
    )


remote_sensing_agent = LlmAgent(
    name="remote_sensing_agent",
    model="gemini-3.5-flash",
    instruction=_instruction,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[_SERVER_PATH],
                    env={**os.environ},
                ),
                timeout=60.0,  # GEE queries involve multiple round-trips; 5s default times out
            )
        )
    ],
    output_key="ndvi_result",
    include_contents="none",
)
