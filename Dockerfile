FROM python:3.10-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Ensure the server can be found
ENV PYTHONPATH=/app

# HF Spaces requires port 7860 for Docker SDK spaces
EXPOSE 7860

# Run the FastAPI application
CMD ["uv", "run", "python3", "server/app.py"]
