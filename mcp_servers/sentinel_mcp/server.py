import json
import asyncio
import sys
import os

# ensure project root is on sys.path when run as a subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_servers.sentinel_mcp import tools

server = Server("sentinel-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_ndvi_trend",
            description=(
                "Returns a time-series of NDVI values for a field location from "
                "Sentinel-2 imagery via Google Earth Engine. "
                "Use for tracking vegetation health trends over time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the field center (-90 to 90)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the field center (-180 to 180)",
                    },
                    "buffer_meters": {
                        "type": "integer",
                        "description": "Half-width of square buffer around point in meters (default 100)",
                        "default": 100,
                    },
                    "lookback_days": {
                        "type": "integer",
                        "description": "Number of days to look back for imagery (default 60)",
                        "default": 60,
                    },
                    "max_cloud_pct": {
                        "type": "integer",
                        "description": "Maximum cloud cover percentage to accept (default 20)",
                        "default": 20,
                    },
                    "geojson": {
                        "type": "string",
                        "description": "Optional GeoJSON string (Polygon, Feature, or FeatureCollection) defining the exact field boundary. When provided, latitude/longitude/buffer_meters are ignored.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_field_snapshot",
            description=(
                "Returns NDVI statistics (mean, min, max) for the most recent "
                "cloud-free Sentinel-2 image at a field location. "
                "Use for a quick current-state health check."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the field center (-90 to 90)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the field center (-180 to 180)",
                    },
                    "buffer_meters": {
                        "type": "integer",
                        "description": "Half-width of square buffer around point in meters (default 100)",
                        "default": 100,
                    },
                    "max_cloud_pct": {
                        "type": "integer",
                        "description": "Maximum cloud cover percentage to accept (default 20)",
                        "default": 20,
                    },
                    "geojson": {
                        "type": "string",
                        "description": "Optional GeoJSON string defining the exact field boundary. When provided, latitude/longitude/buffer_meters are ignored.",
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_ndvi_trend":
            result = tools.run_get_ndvi_trend(arguments)
        elif name == "get_field_snapshot":
            result = tools.run_get_field_snapshot(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except ValueError as e:
        result = {"error": f"Invalid input: {e}"}
    except Exception as e:
        result = {"error": f"GEE query failed: {e}"}

    return [TextContent(type="text", text=json.dumps(result))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
