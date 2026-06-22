# FarmSight — Crop Health Diagnosis Agent

FarmSight is a multi-agent system that investigates crop stress for paddy farmers in Kerala/Palakkad. Given a field location and a question ("Why are my leaves turning yellow?"), it pulls Sentinel-2 satellite imagery and historical rainfall from Open-Meteo, then reasons across both data sources — like an agronomist would — to produce a plain-language diagnosis and action plan.

It is not a dashboard. It is an investigation.

---

## Architecture

```
Farmer input (lat/lon + question)
            │
            ▼
   Coordinator (SequentialAgent)
       │            │
       ▼            ▼
Remote Sensing   Weather Agent
   Agent
       │            │
       ▼            ▼
  sentinel_mcp   weather_mcp
  (GEE/Sentinel-2 (Open-Meteo
   NDVI series)    rainfall)
       │            │
       └─────┬──────┘
             ▼
     Synthesis Agent
  (reads crop_profile.json,
   reasons via SKILL.md workflow)
             │
             ▼
   Diagnosis + Action Plan
```

- **Coordinator** — `SequentialAgent` that runs the three specialists in order and wires session state between them.
- **Remote Sensing Agent** — wraps `sentinel_mcp` via ADK `McpToolset`. Returns raw NDVI time-series; no crop logic.
- **Weather Agent** — wraps `weather_mcp` via ADK `McpToolset`. Returns 30-day rainfall and anomaly indicator; no crop logic.
- **Synthesis Agent** — the only agent that reads `crop_profile.json` (paddy growth stages, NDVI norms, water requirements). Produces the final diagnosis via Gemini using the `skills/crop-diagnosis/SKILL.md` reasoning workflow.
- **MCP servers** — both `sentinel_mcp` and `weather_mcp` run as stdio subprocesses launched by ADK. They validate all inputs at the server boundary before calling external APIs.

---

## Prerequisites

- **Python 3.14+** with [uv](https://docs.astral.sh/uv/) (`brew install uv` or `pip install uv`)
- **Gemini API key** — from [Google AI Studio](https://aistudio.google.com/)
- **Google Earth Engine service account** — requires manual GCP setup (see below)

### Google Earth Engine service account setup

This is a one-time, human-only step that cannot be scripted.

1. Create or select a GCP project and enable the **Earth Engine API**:  
   `https://console.cloud.google.com/apis/library/earthengine.googleapis.com`

2. Create a **service account** in IAM & Admin → Service Accounts. Grant it the **Earth Engine Resource Viewer** role (or register it as an Earth Engine user at step 3).

3. Register the service account with Earth Engine at:  
   `https://signup.earthengine.google.com/` — choose "Service Account" when prompted.

4. Create and download a **JSON key** for the service account. Store it somewhere safe (e.g., `../keys/your-sa-key.json`). Never commit it.

5. Record the service account **email** (e.g., `sa-name@project-id.iam.gserviceaccount.com`).

---

## Setup

```bash
# 1. Install dependencies
cd farmsight
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your actual values:
#   GEE_SERVICE_ACCOUNT_KEY_PATH=/absolute/path/to/your-sa-key.json
#   GEE_SERVICE_ACCOUNT_EMAIL=sa-name@project-id.iam.gserviceaccount.com
#   GOOGLE_API_KEY=your_gemini_api_key
```

---

## Running

### Demo (Palakkad paddy field, one command)

```bash
uv run python main.py --demo
```

### Custom location + question

```bash
uv run python main.py \
  --lat 10.7867 --lon 76.6548 \
  --question "Why are my paddy leaves turning yellow?"
```

### With an exact field boundary (GeoJSON)

```bash
uv run python main.py \
  --geojson my_field.geojson \
  --question "How is my crop doing?"
```

Accepted GeoJSON types: `Polygon`, `Feature`, `FeatureCollection`. The first feature is used for FeatureCollections. A warning is printed if the polygon spans more than ~10 km (likely not a single field).

Without `--geojson`, a 100 m square buffer around the lat/lon is used. This is a stated simplification — it is not real field-boundary detection.

### All flags

| Flag | Default | Description |
|---|---|---|
| `--lat` | — | Field latitude (-90 to 90) |
| `--lon` | — | Field longitude (-180 to 180) |
| `--buffer-m` | 100 | Buffer radius in metres around lat/lon |
| `--question` | "What is the crop health status?" | Your question about the crop |
| `--geojson` | — | Path to GeoJSON file for exact field boundary |
| `--demo` | — | Runs with hardcoded Palakkad coordinates |

---

## Docker

Build and run the demo:

```bash
docker compose up
```

Run a custom query:

```bash
docker compose run farmsight uv run python main.py \
  --lat 10.7867 --lon 76.6548 \
  --question "Why are leaves yellowing?"
```

The `docker-compose.yml` reads `GOOGLE_API_KEY`, `GEE_SERVICE_ACCOUNT_EMAIL`, and `GEE_SERVICE_ACCOUNT_KEY_PATH` from the host `.env` file, then mounts the key file into the container at `/secrets/gee-key.json`.

> **Architecture note:** Both MCP servers (`sentinel_mcp`, `weather_mcp`) use stdio transport and are launched as subprocesses by their respective ADK agents inside the same container. They do not expose network ports. Separate containers per MCP server would require switching to HTTP/SSE transport, which is not implemented in this version.

---

## Output format

```
════════════════════════════════════════════════════════════
  FarmSight — Crop Health Report
  Date   : 2026-06-22
  Field  : point 10.7867°N 76.6548°E  (buffer 100m)
  Season : kharif  |  ~21 days after sowing
════════════════════════════════════════════════════════════

  SATELLITE DATA (Sentinel-2 NDVI)
  Latest image : 2026-05-12  (40 days ago)
    2026-04-22  NDVI=0.461  cloud=4%
    2026-05-02  NDVI=0.488  cloud=8%
    ...

  RAINFALL (last 30 days — Open-Meteo)
  Total: 312 mm  |  Status: EXCESS

  DIAGNOSIS & RECOMMENDATION
  --------------------------------------------------------
  Based on the available Sentinel-2 imagery (most recent:
  2026-05-12, 40 days ago due to monsoon cloud cover)...
════════════════════════════════════════════════════════════
```

---

## Project structure

```
farmsight/
├── main.py                          # CLI entrypoint + report formatter
├── agents/
│   ├── coordinator.py               # SequentialAgent orchestrator
│   ├── remote_sensing.py            # Wraps sentinel_mcp via McpToolset
│   ├── weather_agent.py             # Wraps weather_mcp via McpToolset
│   ├── synthesis.py                 # Gemini reasoning agent
│   └── runner.py                    # InMemoryRunner wiring
├── mcp_servers/
│   ├── sentinel_mcp/                # Sentinel-2 GEE MCP server (stdio)
│   │   ├── server.py
│   │   ├── tools.py                 # get_ndvi_trend, get_field_snapshot
│   │   ├── gee_client.py            # GEE auth + NDVI computation
│   │   └── cache.py                 # Dev-only file cache (avoids re-querying GEE)
│   └── weather_mcp/                 # Open-Meteo MCP server (stdio)
│       ├── server.py
│       ├── tools.py                 # get_rainfall_trend
│       └── openmeteo_client.py
├── skills/crop-diagnosis/
│   ├── SKILL.md                     # Synthesis reasoning workflow
│   ├── references/ndvi_norms.md     # Paddy NDVI ranges per growth stage
│   └── assets/output_template.md   # Diagnosis output format
├── data/crop_profile.json           # Paddy growth stages + water requirements
├── scripts/verify_phase1.py         # Phase 1 gate: GEE NDVI verification
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── BUILD_NOTES.md                   # Deviations from PRD and whitepapers
```

---

## Known limitations

| Limitation | Notes |
|---|---|
| Field geometry | 100 m buffer around lat/lon by default — not real field-boundary detection. Use `--geojson` for exact boundaries. |
| Imagery staleness | Sentinel-2 NDVI can be 40+ days stale during Kerala monsoon season (heavy cloud cover). The system reports `data_recency_days` honestly and does not silently use clouded images. |
| Sowing date | Defaults to season start (Jun 1 for Kharif, Nov 1 for Rabi). Growth stage estimates are approximate unless the farmer's actual sowing date is known. |
| Crop support | Only paddy is implemented in `data/crop_profile.json`. The config structure supports additional crops without changing the agent code. |
| Season coverage | Kharif (Jun–Oct) and Rabi (Nov–Mar) for Kerala paddy. Regions or crops with different calendars would need updated season logic in `coordinator.py`. |

---

## Environment variables

| Variable | Description |
|---|---|
| `GEE_SERVICE_ACCOUNT_KEY_PATH` | Absolute path to the GEE service account JSON key file |
| `GEE_SERVICE_ACCOUNT_EMAIL` | Service account email (e.g., `sa@project.iam.gserviceaccount.com`) |
| `GOOGLE_API_KEY` | Gemini API key from Google AI Studio |

See `.env.example` for the template.
