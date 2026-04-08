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

# Create the standard OpenEnv app — this registers /reset, /step, /state, /health, /schema etc.
# When ENABLE_WEB_INTERFACE=true (set by openenv push), it also adds Gradio at /web.
# We must NOT add any catch-all routes that would shadow the OpenEnv API routes.
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
# Only serve frontend files at a dedicated sub-path to avoid conflicting with API routes.
# The OpenEnv web interface already serves at / and /web when ENABLE_WEB_INTERFACE=true.
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Serve individual frontend files at explicit paths (no catch-all mount)
@app.get("/dashboard", tags=["Frontend"])
async def read_dashboard():
    """Serve the NeonGrid dashboard."""
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount frontend assets under /static to avoid conflicts
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")

logger.info("NeonGrid Architectural Server mounted.")

def main():
    import uvicorn
    # HF Spaces uses port 7860; locally fallback to 7860 as well
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Starting NeonGrid on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
