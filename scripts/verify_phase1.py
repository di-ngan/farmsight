"""
Phase 1 gate script — no agent framework.
Calls the sentinel MCP server directly via a bare MCP client and prints the NDVI series.
Run from the farmsight/ directory:
    uv run python scripts/verify_phase1.py
"""

import asyncio
import json
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEMO_LAT = 10.7867
DEMO_LON = 76.6548


async def main():
    server_script = os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "sentinel_mcp", "server.py")
    server_script = os.path.abspath(server_script)

    params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env={**os.environ},
    )

    print(f"Connecting to sentinel MCP server at {server_script}...\n")

    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()

            print("=== get_ndvi_trend ===")
            result = await session.call_tool(
                "get_ndvi_trend",
                {
                    "latitude": DEMO_LAT,
                    "longitude": DEMO_LON,
                    "lookback_days": 60,
                    "max_cloud_pct": 20,
                },
            )
            data = json.loads(result.content[0].text)
            print(json.dumps(data, indent=2))

            print("\n=== Validation ===")
            if "error" in data:
                print(f"FAIL: error returned: {data['error']}")
                sys.exit(1)

            series = data.get("ndvi_series", [])
            if not series:
                print("FAIL: ndvi_series is empty — no cloud-free imagery found in 60-day window")
                print(f"Warning: {data.get('warning')}")
                sys.exit(1)

            print(f"OK: {len(series)} image(s) in series")
            print(f"OK: latest image date = {data['latest_image_date']} ({data['data_recency_days']} days ago)")

            bad = [e for e in series if not (0.0 <= e["ndvi_mean"] <= 1.0)]
            if bad:
                print(f"WARN: {len(bad)} entries have NDVI outside 0–1 range: {bad}")
            else:
                ndvi_vals = [e["ndvi_mean"] for e in series]
                print(f"OK: NDVI means range {min(ndvi_vals):.3f}–{max(ndvi_vals):.3f}")

            print("\nManual check: inspect dates and NDVI values above.")
            print("Expected for active paddy: ndvi_mean roughly 0.2–0.8")
            print("Expected for recently flooded/bare: 0.05–0.3")


asyncio.run(main())
