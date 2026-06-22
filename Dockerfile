FROM python:3.14-slim

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies before copying source (improves layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY . .

# The GEE service account key is mounted at runtime via docker-compose volume.
# MCP servers (sentinel_mcp, weather_mcp) are launched as subprocesses by ADK
# agents — they do not need separate exposed ports.
ENV GEE_SERVICE_ACCOUNT_KEY_PATH=/secrets/gee-key.json

CMD ["uv", "run", "python", "main.py", "--demo"]
