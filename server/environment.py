import os
import random
import math
from uuid import uuid4
from datetime import datetime, timedelta

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import GridAction, GridObservation
except ImportError:
    from models import GridAction, GridObservation

class NeonGridEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.battery = 50.0  # Start at 50%
        self.comfort = 1.0   # Start with maximum comfort
        self.sim_time = datetime(2026, 4, 8, 8, 0)  # Start at 8:00 AM
        self.total_cost = 0.0
        self.weather = "sunny" # Default value
        self.task_level = os.getenv("SUPPORT_TASK", "easy").lower()
        self.directives = None

    def _get_base_demand(self):
        # Demand peaks in morning (9am) and evening (7pm)
        hour = self.sim_time.hour
        base = 50 + 40 * math.sin(math.pi * (hour - 6) / 12)
        return max(30, base)

    def _get_solar_potential(self, weather):
        hour = self.sim_time.hour
        if hour < 6 or hour > 18: return 0.0
        
        # Bell curve for sun
        potential = 100 * math.sin(math.pi * (hour - 6) / 12)
        
        modifiers = {"sunny": 1.0, "cloudy": 0.4, "stormy": 0.1}
        return potential * modifiers.get(weather, 1.0)

    def _get_grid_price(self, hour):
        # Prices spike during evening peak
        if 17 <= hour <= 21: return 0.50
        if 8 <= hour <= 10: return 0.30
        return 0.10

    def reset(self) -> GridObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.battery = 50.0
        self.comfort = 1.0
        self.total_cost = 0.0
        self.directives = None
        
        # Difficulty adjusts the starting conditions
        self.task_level = os.getenv("SUPPORT_TASK", "easy").lower()
        
        if self.task_level == "easy":
            self.sim_time = datetime(2026, 4, 8, 10, 0) # Sunny morning
            self.weather = "sunny"
        elif self.task_level == "medium":
            self.sim_time = datetime(2026, 4, 8, 17, 0) # Evening peak start
            self.weather = "cloudy"
        else: # hard
            self.sim_time = datetime(2026, 4, 8, 19, 0) # Deep peak
            self.weather = "stormy"

        return self._generate_obs("System online. Grid Architect initialized.")

    def step(self, action: GridAction) -> GridObservation:
        self._state.step_count += 1
        self.sim_time += timedelta(minutes=15)
        
        # 1. Calculate Demand
        demand = self._get_base_demand()
        if action.consumption_mode == "low":
            demand *= 0.7
            self.comfort = max(0.4, self.comfort - 0.05)
        elif action.consumption_mode == "high":
            demand *= 1.3
            self.comfort = min(1.0, self.comfort + 0.02)
        else: # normal
            self.comfort = min(1.0, self.comfort + 0.01)

        # 2. Calculate Solar
        solar = self._get_solar_potential(self.weather)
        
        # 3. Handle Battery
        net_flow = 0
        if action.battery_mode == "charge" and self.battery < 100:
            charge_rate = 10.0
            net_flow = charge_rate
            self.battery = min(100, self.battery + (charge_rate / 4)) # /4 because 15 min steps
        elif action.battery_mode == "discharge" and self.battery > 0:
            discharge_rate = 20.0
            net_flow = -discharge_rate
            self.battery = max(0, self.battery - (discharge_rate / 4))

        # 4. Energy Balance
        # Total needed = Demand + Battery Charging
        total_needed = demand + (net_flow if net_flow > 0 else 0)
        # Solar contribution
        from_solar = min(total_needed, solar)
        remaining_needed = total_needed - from_solar
        
        # Battery contribution (if discharging)
        from_battery = 0
        if net_flow < 0:
            from_battery = min(remaining_needed, abs(net_flow))
            remaining_needed -= from_battery
            
        # Grid covers the rest
        from_grid = remaining_needed
        grid_price = self._get_grid_price(self.sim_time.hour)
        step_cost = from_grid * grid_price
        self.total_cost += step_cost

        # 5. Reward Calculation
        # Reward is high for low cost AND high comfort
        cost_penalty = step_cost / 50.0 # Normalized
        reward = (self.comfort * 0.5) + (max(0, 0.5 - cost_penalty))
        
        # Finish conditions
        done = self._state.step_count >= 20 # 5 hours simulated
        
        status = f"Consuming {demand:.1f}MW. Cost: ${step_cost:.2f}. Battery at {self.battery:.1f}%."

        obs = self._generate_obs(status)
        obs.reward = reward
        obs.done = done
        return obs

    def _generate_obs(self, msg) -> GridObservation:
        return GridObservation(
            grid_price=self._get_grid_price(self.sim_time.hour),
            solar_output=self._get_solar_potential(self.weather),
            battery_level=self.battery,
            district_demand=self._get_base_demand(),
            comfort_index=self.comfort,
            weather=self.weather,
            status_message=msg,
            current_time=self.sim_time.strftime("%H:%M"),
            done=False,
            reward=0.0,
            directives=self.directives
        )

    @property
    def state(self) -> State:
        return self._state
