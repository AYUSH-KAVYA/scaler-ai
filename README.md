---
title: NeonGrid
emoji: 🏙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# NeonGrid | AI Energy Architect

A legendary OpenEnv environment for training AI agents to manage futuristic sustainable power grids.

## The Mission
You are the central AI brain of a high-tech city district. Your goal is to balance **Energy Costs**, **Citizen Comfort (HVAC)**, and **Battery Reserves**. You must navigate price spikes, solar fluctuations, and storms to keep the city glowing and the citizens happy.

## Action & Observation Spaces

### Observation Space
- `grid_price`: Current cost of energy ($/MW).
- `solar_output`: Real-time renewable generation.
- `battery_level`: 0-100% capacity.
- `district_demand`: What the citizens need.
- `comfort_index`: 0.0-1.0 (happiness).
- `weather`: 'sunny', 'cloudy', 'stormy'.
- `current_time`: HH:MM in the simulation.

### Action Space
- `consumption_mode`: 
    - `low`: Cuts demand (saves money, hurts comfort).
    - `normal`: Balanced.
    - `high`: Boosts comfort (uses more power).
- `battery_mode`: `charge`, `discharge`, `idle`.
- `source_priority`: `solar` or `grid`.

## Task Protocols
- **Easy (Bright Day)**: Start at 10:00 AM. Perfect solar conditions. Agent learns basic battery charging.
- **Medium (Evening Peak)**: Start at 5:00 PM. Solar is fading, prices are rising. Requires strategic battery discharge.
- **Hard (Storm Surge)**: Start at 7:00 PM during a storm. Zero solar, max prices. Requires extreme trade-offs between cost and comfort.

## Setup & Legendary Frontend
1. **Build & Run**:
   ```bash
   docker build -t neongrid -f server/Dockerfile .
   docker run -p 8000:8000 neongrid
   ```
2. **Access Dashboard**: Open `http://localhost:8000` in your browser for the **Cyberpunk Control Center**.

## Evaluation Baseline
The `inference.py` script provides the standard telemetry required for evaluation. It utilizes a heuristic fallback if API limits are reached to ensure the environment's logic is always verifiable.
```bash
python inference.py
```
To run the evaluation, make sure to set the `HF_TOKEN` environment variable locally.
