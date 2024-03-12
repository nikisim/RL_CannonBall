# RL_CannonBall

This repository contains RL env with Cannon Ball [in progress]

## Installation
Для того, чтобы установить среду необходимо выполнить следующую команду:
```
pip install -e .
```

## Basic Usage
```
import gym
import gym_CannonBall
import math

env = gym.make('gym_CannonBall/CannonEnv-v0')

env.reset()
action = env.action_space.sample()
obs, reward, done, _,info = env.step(action)
print(f"Observation: {obs}, Reward: {reward}")
env.close()
```

## About Cannon env
Среда представляет собой упрощенную модель выстрела ядра из пушки по заданному углу и расстоянию до цели.

| Environment Id | Observation Space |Action Space| Reward Range | 
| -------------| ------ |------ | -----------|
| CannonEnv-v0 |Box(1,2)|Box(1,)|(-100, 500) | 

### State
Наблюдением является заданный угол и расстояние до цели, которые в свою очередь явлюятся числами типа float32.
 
```
state, _ = env.reset()
#state = [angle, distance_to_target]
```

### Action
Действием является начальная скорость ядра (число float32).

### Reward
Награда задается как:
```
reward = max(-100, 500 - abs(diff between target and current ball coordinate))
```

