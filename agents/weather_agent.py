import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams, StdioServerParameters

_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "weather_mcp", "server.py")
)


def _instruction(ctx) -> str:
    lat = ctx.state.get("input_lat")
    lon = ctx.state.get("input_lon")
    return (
        "You are the Weather Agent for FarmSight. "
        f"Call the get_rainfall_trend tool with latitude={lat}, longitude={lon}, "
        "lookback_days=60. "
        "Return ONLY the raw JSON result from the tool — no extra commentary."
    )


weather_agent = LlmAgent(
    name="weather_agent",
    model="gemini-3.5-flash",
    instruction=_instruction,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[_SERVER_PATH],
                    env={**os.environ},
                )
            )
        )
    ],
    output_key="rainfall_result",
    include_contents="none",
)
