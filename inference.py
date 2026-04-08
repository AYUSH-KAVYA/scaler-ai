"""
NeonGrid AI Energy Architect — Inference Script
Connects to the deployed OpenEnv environment via HTTP and runs an AI agent.
Uses only stdlib + openai (the only allowed external dependency).
"""
import subprocess
import os
import sys
import json
import urllib.request
import urllib.error
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Auto-install openai if not available
try:
    from openai import OpenAI
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
    from openai import OpenAI


# ── Environment Configuration ──────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# The URL of the deployed environment (HF Space or local)
ENV_URL = os.getenv("ENV_URL", "https://ayush-kr-neongrid-env.hf.space")

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN environment variable not set. Aborting.")
    sys.exit(1)

TASK_NAME = os.getenv("SUPPORT_TASK", "easy")
BENCHMARK = "neongrid_env"
MAX_STEPS = 20
TEMPERATURE = 0.0
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.5

# ── System Prompt ──────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the AI Energy Architect for NeonGrid.
Your goal is to manage a city's energy to maximize citizen comfort while minimizing grid costs.

ACTION SCHEMA (respond with ONLY this JSON, no extra text):
{
  "consumption_mode": "low" | "normal" | "high",
  "battery_mode": "charge" | "discharge" | "idle",
  "source_priority": "solar" | "grid"
}

TIPS:
- If grid_price is high (>= 0.3), use "low" consumption and "discharge" the battery.
- If grid_price is low (< 0.3) and solar is high, use "normal" or "high" consumption and "charge" the battery.
- If there is a "directives" string, PRIORITIZE it over all other logic.
Always respond with a valid JSON object only."""

# ── Logging (strict OpenEnv format) ────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# ── Environment HTTP Client (stdlib only) ──────────────────────────
def _post_json(url: str, data: dict) -> dict:
    """POST JSON to a URL using only stdlib urllib."""
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def env_reset(base_url: str) -> dict:
    data = _post_json(f"{base_url}/reset", {})
    return data.get("observation", data)

def env_step(base_url: str, action: dict) -> dict:
    return _post_json(f"{base_url}/step", {"action": action})

# ── Action Parsing ─────────────────────────────────────────────────
def parse_action(text: str) -> dict:
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception:
        return {"consumption_mode": "normal", "battery_mode": "idle", "source_priority": "solar"}

def get_model_action(client: OpenAI, obs: dict) -> dict:
    user_prompt = json.dumps({
        "time": obs.get("current_time", ""),
        "grid_price": obs.get("grid_price", 0),
        "solar": obs.get("solar_output", 0),
        "battery": obs.get("battery_level", 0),
        "comfort": obs.get("comfort_index", 0),
        "weather": obs.get("weather", ""),
        "status": obs.get("status_message", ""),
        "directives": obs.get("directives", None),
    })
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return parse_action(text)
    except Exception:
        price = obs.get("grid_price", 0)
        if price >= 0.3:
            return {"consumption_mode": "low", "battery_mode": "discharge", "source_priority": "solar"}
        return {"consumption_mode": "normal", "battery_mode": "charge", "source_priority": "solar"}

# ── Main Loop ──────────────────────────────────────────────────────
def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env_reset(ENV_URL)

        for step in range(1, MAX_STEPS + 1):
            action = get_model_action(client, obs)
            action_str = f"cons:{action.get('consumption_mode','?')},batt:{action.get('battery_mode','?')}"

            resp = env_step(ENV_URL, action)
            obs = resp.get("observation", resp)
            reward = resp.get("reward", 0.0) or 0.0
            done = resp.get("done", False)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            if done:
                break

        score = sum(rewards) / len(rewards) if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()
