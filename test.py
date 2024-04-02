import gym
import gym_CannonBall
import math
import sys
import warnings
import torch
import numpy as np
from DDPG.DDPG import DDPG,Actor,Critic,ReplayBuffer

if __name__ == "__main__":

    actor = torch.load()
    critic = torch.load()


    # # ignore warnings
    # if not sys.warnoptions:
    #     warnings.simplefilter("ignore")
    # env = gym.make('gym_CannonBall/CannonEnv-v0')

    # obs = env.reset()
    # done = False
    # print(obs)
    # angle = obs[0]
    # target = obs[1]
    # action = env.action_space.sample()
    # print(action)
    # obs, reward, done, info = env.step(action)
    # print(f'Observation angle: {obs[0]:.1f}')
    # print(f'Observation new dist to target: {obs[1]:.1f}')
    # print(f'Reward: {reward:.1f}')

    # env.close()