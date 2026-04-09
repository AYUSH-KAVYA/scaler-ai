"""
Grader for the 'tutorial' task — Basic Grid Stabilization.

Evaluates foundational agent competence in a high-solar, low-demand environment.
The agent should maintain stable voltage and high citizen comfort.
"""

def grade(trajectory: list) -> float:
    """
    Grade the agent's trajectory for the tutorial task.

    Args:
        trajectory: List of (action, observation) dicts from the episode.

    Returns:
        Score between 0.0 and 1.0.
    """
    if not trajectory:
        return 0.0

    total_reward = 0.0
    steps = 0

    for step_data in trajectory:
        # OpenEnv typically passes a list of (action, observation) tuples
        # but sometimes the data structure can vary slightly in different versions.
        # This implementation is robust to both direct dicts and wrapped dicts.
        obs = step_data.get("observation", step_data) if isinstance(step_data, dict) else step_data[1]
        
        # Extract reward from observation
        reward = obs.get("reward", 0.0)
        if reward is None:
            reward = 0.0
        total_reward += float(reward)
        steps += 1

    if steps == 0:
        return 0.0

    avg_reward = total_reward / steps
    
    # Normalize to 0-1 range
    score = max(0.0, min(1.0, avg_reward))
    return score
