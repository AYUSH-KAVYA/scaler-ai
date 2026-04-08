# AI Training in NeonGrid: OpenEnv Guide

This guide explains how your AI model interacts with the NeonGrid environment and how the standard `step()`, `reset()`, and `reward` system works.

## 🕹️ The OpenEnv Interface

NeonGrid follows the **OpenEnv** standard, which models the interaction between an AI and an environment as a series of cycles.

### 1. `reset()` - The Beginning
Before an AI starts learning, it needs a clean slate.
- **What it does**: Resets the city to its initial state (e.g., 8:00 AM, 50% battery).
- **Return**: A `GridObservation` containing the current "State of the World."

### 2. `step(action)` - The Cycle
This is the heart of the environment. The agent takes an action, and the environment moves forward in time (15 minutes).
- **Input**: A `GridAction` (Consumption Mode, Battery Mode).
- **Return**: 
    - `Observation`: What the world looks like now.
    - `Reward`: How "good" or "bad" the action was.
    - `Done`: A boolean flag—is the simulation over?

---

## 🧠 How the AI "Learns"

Training an AI is like teaching a dog: you give it a "treat" (Reward) when it does something good and a "penalty" when it does something bad.

### Reinforcement Learning (RL)
In a real training loop, an algorithm (like PPO or DQN) would follow these steps:
1. **Observe**: "The grid price is $0.50 (expensive) and the battery is full."
2. **Act**: The agent decides to *discharge* the battery.
3. **Reward**: The environment sees the cost went down and gives a **High Reward (+1.0)**.
4. **Learn**: The agent internalizes: *"When price is high, discharging battery = Good reward."*

### Prediction via LLM (Inference)
The current `inference.py` uses a Large Language Model. Instead of training through millions of steps, it "learns" from the context:
- It receives the current `Observation` in its system prompt.
- It uses its pre-existing knowledge of energy management to predict the best JSON `Action`.

---

## 🛠️ Using the API Programmatically

If you want to build your own agent, you can interact with the environment like this:

```python
from server.environment import NeonGridEnvironment
from models import GridAction

env = NeonGridEnvironment()
obs = env.reset()

for _ in range(20):
    # Your AI Logic here
    action = GridAction(consumption_mode="low", battery_mode="discharge", source_priority="solar")
    
    # Move the world forward
    obs = env.step(action)
    
    print(f"Time: {obs.current_time} | Reward: {obs.reward}")
    if obs.done: break
```

## 🏆 Reward Calculation
In NeonGrid, the reward is calculated as:
`Reward = (Comfort * 0.5) + (Efficiency * 0.5)`
- **Comfort**: Keep citizens happy (Normal/High consumption).
- **Efficiency**: Avoid buying expensive grid power.
