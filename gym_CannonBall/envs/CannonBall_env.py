import gymnasium as gym
from gym import spaces
import numpy as np
import math

class CannonEnv(gym.Env):

    def __init__(self):
        super(CannonEnv, self).__init__()
        
        # Define action and observation space
        # They must be gym.spaces objects
        # Example when using continuous actions:
        # self.action_space = spaces.Box(low=0, high=50, shape=(1,), dtype=np.float32)
        n_actions = 5
        #actions = np.linspace(0,100,n_actions)
        self.action_space = spaces.Discrete(n_actions)
        
        # Example for using continuous observations (angle in radians and distance):
        self.observation_space = spaces.Box(low=np.array([0, 0]), high=np.array([np.pi/2, 1000]), dtype=np.float32)
        
        self.info = {}
        # Initialize state
        self.angle = None
        self.distance_to_target = None
        self.current_distance = None
        self.target_distance = None  # Random target distance for each episode
        self.episode_reward = 0
        self.episode_length = 0

    def step(self, action: float):
        # Execute one time step within the environment
        #speed = action[0]
        self._take_shot((action+1)*10)
        
        if not self.action_space.contains(action):
            raise ValueError(f"Action '{action}' is not in action_space")
        
        # Calculate reward, done, and info
        reward = self._calculate_reward()
        done = True  # In this case, we end the episode after one shot
                
        self.episode_reward += reward
        self.episode_length += 1

        if done:
            # Populate the info dictionary with episodic information
            self.info['final_info'] = {
                'episode': {
                    'r': self.episode_reward,
                    'l': self.episode_length,
                }
                # Include any other information you want to track
            }
            # Reset episode information
            self.episode_reward = 0
            self.episode_length = 0

        # Return the next observation, reward, done, and info
        return self._get_obs(), reward, done, False, self.info

    def reset(self):
        # Reset the state of the environment to an initial state
        self.angle = np.random.uniform(low=0, high=np.pi/2)
        self.distance_to_target = np.random.uniform(low=500, high=1000)  # Random target distance for each episode
        return self._get_obs(),self.info

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        pass  # For simplicity, we are not implementing rendering here

    def _get_obs(self):
        # Helper method to get the current observation
        return np.array([self.angle, self.distance_to_target], dtype=np.float32)

    def _take_shot(self, speed:float):
        # Helper method to simulate taking a shot
        # You would implement the physics of the cannon shot here
        # For now, we'll just set the distance to a random value
        # self.distance_to_target = np.random.uniform(low=0, high=self.target_distance)
        self.current_distance = speed**2 * math.sin(2*self.angle)/(9.80665)
        # make some noise
        self.current_distance += np.random.normal(0,1,1)[0]
        # print(f'Current dist: {self.current_distance:.1f}')
        self.distance_to_target = self.distance_to_target - self.current_distance

    def _calculate_reward(self):
        # Helper method to calculate the reward
        # For now, we'll just return a reward based on how close the shot is to the target
        reward = max(-100, 500 - abs(self.distance_to_target - self.current_distance))
        #reward = 1/abs(self.target_distance - self.current_distance)
        return reward