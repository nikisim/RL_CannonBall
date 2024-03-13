import numpy as np
import gym
import CannonEnv  # Make sure to import your CannonEnv class

def train_cem(env, n_iterations=100, batch_size=50, elite_frac=0.2, initial_std=10.0):
    """
    Train an agent using the cross-entropy method.

    Parameters:
    - env: The environment to train on.
    - n_iterations: Number of training iterations.
    - batch_size: Number of samples per iteration.
    - elite_frac: Fraction of samples to use as elite set.
    - initial_std: Initial standard deviation of the action distribution.
    """
    n_elite = int(batch_size * elite_frac)

    # Initialize mean and standard deviation of the action distribution
    mean = np.zeros(env.action_space.shape)
    std = np.full(env.action_space.shape, initial_std)

    for iteration in range(n_iterations):
        # Sample actions
        actions = np.random.normal(mean, std, size=(batch_size, env.action_space.shape[0]))

        # Evaluate actions
        rewards = np.array([evaluate_action(env, action) for action in actions])

        # Select elite samples
        elite_idxs = rewards.argsort()[-n_elite:]
        elite_actions = actions[elite_idxs]

        # Update distribution parameters
        mean = elite_actions.mean(axis=0)
        std = elite_actions.std(axis=0)

        print(f"Iteration {iteration + 1}/{n_iterations}: mean reward = {rewards.mean()}")

    return mean

def evaluate_action(env, action):
    """
    Evaluate a single action in the environment.

    Parameters:
    - env: The environment to evaluate the action in.
    - action: The action to evaluate.

    Returns:
    - reward: The reward obtained from the action.
    """
    observation, info = env.reset()
    observation, reward, done, _, info = env.step(action)
    return reward

if __name__ == "__main__":
    env = CannonEnv()  # Initialize your environment
    optimal_action = train_cem(env)
    print(f"Optimal initial speed found: {optimal_action}")
