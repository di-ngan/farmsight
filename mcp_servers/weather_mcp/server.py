import json
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_servers.weather_mcp import tools

server = Server("weather-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_rainfall_trend",
            description=(
                "Returns daily rainfall data and a 30-day anomaly indicator for a "
                "location, sourced from the Open-Meteo historical archive. "
                "Use to assess drought, normal, or flood conditions for crop diagnosis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location (-90 to 90)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location (-180 to 180)",
                    },
                    "lookback_days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 60)",
                        "default": 60,
                    },
                },
                "required": ["latitude", "longitude"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_rainfall_trend":
            result = await tools.run_get_rainfall_trend(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except ValueError as e:
        result = {"error": f"Invalid input: {e}"}
    except Exception as e:
        result = {"error": f"Weather query failed: {e}"}

    return [TextContent(type="text", text=json.dumps(result))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
