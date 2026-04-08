import logging
import os
import sys

# Ensure the root directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Body
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

# --- PERSISTENT STATE LOGIC FOR FRONTEND ---
# The standard 'create_app' is stateless over HTTP. 
# For your "Legendary" dashboard, we'll maintain a single persistent environment instance
# so that your clicks actually change the state!
GLOBAL_ENV = NeonGridEnvironment()

# Create the standard OpenEnv app
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

# Overwrite /reset and /step to use our GLOBAL_ENV for the dashboard
@app.post("/reset", tags=["Environment Control"])
async def dashboard_reset(task: str = Body(default="easy")):
    # Set task level and reset the global instance
    os.environ["SUPPORT_TASK"] = task
    obs = GLOBAL_ENV.reset()
    return {"observation": obs.model_dump()}

@app.post("/step", tags=["Environment Control"])
async def dashboard_step(action: dict = Body(...)):
    # Parse action and step the global instance
    # OpenEnv standard sends {"action": {...}}
    action_data = action.get("action", action)
    grid_action = GridAction(**action_data)
    obs = GLOBAL_ENV.step(grid_action)
    return {"observation": obs.model_dump()}

@app.post("/command", tags=["Environment Control"])
async def dashboard_command(payload: dict = Body(...)):
    # Update the environment directives
    directive = payload.get("directive", "")
    GLOBAL_ENV.directives = directive
    return {"status": "Directive updated", "directive": directive}

@app.get("/state", tags=["Environment Control"])
async def dashboard_state():
    return {"state": GLOBAL_ENV.state.model_dump(), "observation": GLOBAL_ENV._generate_obs("Syncing state").model_dump()}

# --- FRONTEND SERVING ---
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Mount the frontend directory at root (after API routes)
app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

logger.info("NeonGrid Architectural Server mounted with Persistent Dashboard Support.")

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
