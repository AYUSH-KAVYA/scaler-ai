import logging
import os
import sys

# Ensure the root directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openenv.core.env_server.http_server import create_app

try:
    from models import GridAction, GridObservation
    from server.environment import NeonGridEnvironment
except ImportError:
    from .models import GridAction, GridObservation
    from .environment import NeonGridEnvironment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the standard OpenEnv app — this registers /reset, /step, /state etc.
# We do NOT override these routes so there are no conflicts.
app = create_app(
    NeonGridEnvironment,
    GridAction,
    GridObservation,
)

# Add CORS support for remote machine access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ADDITIONAL ENDPOINTS (non-conflicting) ---

# Persistent env for the command directive feature
GLOBAL_ENV = NeonGridEnvironment()

@app.post("/command", tags=["Environment Control"])
async def dashboard_command(payload: dict = Body(...)):
    """Update the environment directives."""
    directive = payload.get("directive", "")
    GLOBAL_ENV.directives = directive
    return {"status": "Directive updated", "directive": directive}

# --- FRONTEND SERVING ---
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the frontend directory at root (after API routes)
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

logger.info("NeonGrid Architectural Server mounted.")

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
