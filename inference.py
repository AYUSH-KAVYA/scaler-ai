import asyncio
import os
import textwrap
import json
import sys
from typing import List, Optional
from dotenv import load_dotenv

# Load configuration from .env file
load_dotenv()

from openai import OpenAI
from models import GridAction

# Use a model that has better availability or clear free-tier access if possible
# Or shifting to a more robust model name example
# Environment Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct") 

if not HF_TOKEN:
    print("[ERROR] HF_TOKEN environment variable not set. Aborting.")
    sys.exit(1)

TASK_NAME = os.getenv("SUPPORT_TASK", "easy")
BENCHMARK = "neongrid_env"
MAX_STEPS = 20
TEMPERATURE = 0.0
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are the AI Energy Architect for NeonGrid.
    Your goal is to manage a city's energy to maximize citizen comfort while minimizing grid costs.
    
    ACTION SCHEMA:
    {
      "consumption_mode": "low" | "normal" | "high",
      "battery_mode": "charge" | "discharge" | "idle",
      "source_priority": "solar" | "grid"
    }
    
    TIPS:
    - If grid_price is high (>= 0.3), use "low" consumption and "discharge" the battery.
    - If grid_price is low (< 0.3) and solar is high, use "normal" or "high" consumption and "charge" the battery.
    
    DIRECTIVE SYSTEM:
    If the user provides a "directives" string, PRIORITIZE it over all other logic.
    Always respond with a valid JSON object.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(obs) -> str:
    return json.dumps({
        "time": obs.current_time,
        "grid_price": obs.grid_price,
        "solar": obs.solar_output,
        "battery": obs.battery_level,
        "comfort": obs.comfort_index,
        "weather": obs.weather,
        "status": obs.status_message,
        "directives": obs.directives
    })

def parse_action(text: str) -> GridAction:
    try:
        # Extract json safely if model wraps in markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        data = json.loads(text)
        return GridAction(**data)
    except:
        # Fallback heuristic logic if API fails or model halucinates
        if "high" in text.lower():
            return GridAction(consumption_mode="low", battery_mode="discharge", source_priority="solar")
        return GridAction(consumption_mode="normal", battery_mode="idle", source_priority="solar")

async def get_model_action(client: OpenAI, obs) -> GridAction:
    user_prompt = build_user_prompt(obs)
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
    except Exception as exc:
        # If API errors (like 402), return a heuristic action to keep the env running
        if "grid_price" in locals() and obs.grid_price >= 0.3:
            return GridAction(consumption_mode="low", battery_mode="discharge", source_priority="solar")
        return GridAction(consumption_mode="normal", battery_mode="charge", source_priority="solar")

async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    from server.environment import NeonGridEnvironment
    env_instance = NeonGridEnvironment()
    
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env_instance.reset()
        
        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break
                
            action = await get_model_action(client, obs)
            action_str = f"cons:{action.consumption_mode},batt:{action.battery_mode}"
            
            obs = env_instance.step(action)
            
            reward = obs.reward or 0.0
            done = obs.done
            
            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=action_str, reward=reward, done=done, error=None)
            
            if done:
                break
                
        # Calculate normalized score [0, 1]
        score = sum(rewards) / len(rewards) if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
