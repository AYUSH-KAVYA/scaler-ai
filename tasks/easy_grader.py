"""
Grader for the 'easy' task — Bright Day scenario.

Evaluates agent performance on a sunny morning with low grid prices.
A good agent should charge the battery during cheap solar hours
and maintain high comfort.
"""


def grade(trajectory: list) -> float:
    """
    Grade the agent's trajectory for the easy task.

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
        obs = step_data.get("observation", step_data)
        reward = obs.get("reward", 0.0)
        if reward is None:
            reward = 0.0
        total_reward += float(reward)
        steps += 1

    if steps == 0:
        return 0.0

    avg_reward = total_reward / steps

    # Normalize to 0-1 range (rewards are typically 0-1 in this env)
    score = max(0.0, min(1.0, avg_reward))
    return score
