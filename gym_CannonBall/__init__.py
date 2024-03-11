from gym.envs.registration import register

register(
    id="gym_CannonBall/CannonEnv-v0",
    entry_point="gym_CannonBall.envs:CannonEnv",
)
