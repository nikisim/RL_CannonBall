import gym
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import gym_CannonBall
from torch.utils.tensorboard import SummaryWriter


class Actor(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_width, max_action):
        super(Actor, self).__init__()
        self.max_action = max_action
        self.l1 = nn.Linear(state_dim, hidden_width)
        self.l2 = nn.Linear(hidden_width, hidden_width)
        self.l3 = nn.Linear(hidden_width, action_dim)

    def forward(self, s):
        s = F.relu(self.l1(s))
        s = F.relu(self.l2(s))
        a = self.max_action * torch.tanh(self.l3(s))
        return a


class Critic(nn.Module): 
    def __init__(self, state_dim, action_dim, hidden_width):
        super(Critic, self).__init__()
        self.l1 = nn.Linear(state_dim + action_dim, hidden_width)
        self.l2 = nn.Linear(hidden_width, hidden_width)
        self.l3 = nn.Linear(hidden_width, 1)

    def forward(self, s, a):
        q = F.relu(self.l1(torch.cat([s, a], 1)))
        q = F.relu(self.l2(q))
        q = self.l3(q)
        return q


class ReplayBuffer(object):
    def __init__(self, state_dim, action_dim):
        self.max_size = int(1e6)
        self.count = 0
        self.size = 0
        self.s = np.zeros((self.max_size, state_dim))
        self.a = np.zeros((self.max_size, action_dim))
        self.r = np.zeros((self.max_size, 1))
        self.s_ = np.zeros((self.max_size, state_dim))
        self.dw = np.zeros((self.max_size, 1))

    def store(self, s, a, r, s_, dw):
        self.s[self.count] = s
        self.a[self.count] = a
        self.r[self.count] = r
        self.s_[self.count] = s_
        self.dw[self.count] = dw
        self.count = (self.count + 1) % self.max_size  
        self.size = min(self.size + 1, self.max_size)  

    def sample(self, batch_size):
        index = np.random.choice(self.size, size=batch_size) 
        batch_s = torch.tensor(self.s[index], dtype=torch.float)
        batch_a = torch.tensor(self.a[index], dtype=torch.float)
        batch_r = torch.tensor(self.r[index], dtype=torch.float)
        batch_s_ = torch.tensor(self.s_[index], dtype=torch.float)
        batch_dw = torch.tensor(self.dw[index], dtype=torch.float)

        return batch_s, batch_a, batch_r, batch_s_, batch_dw


class DDPG(object):
    def __init__(self, state_dim, action_dim, max_action):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.hidden_width = 32  # The number of neurons in hidden layers of the neural network
        self.batch_size = 32  # batch size
        self.GAMMA = 0.99  # discount factor
        self.TAU = 0.005  # Softly update the target network
        self.lr = 1e-4  # learning rate

        self.actor = Actor(state_dim, action_dim, self.hidden_width, max_action).to(self.device)
        self.actor_target = copy.deepcopy(self.actor).to(self.device)
        self.critic = Critic(state_dim, action_dim, self.hidden_width).to(self.device)
        self.critic_target = copy.deepcopy(self.critic).to(self.device)

        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=self.lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=self.lr)

        self.MseLoss = nn.MSELoss()

    def choose_action(self, s):
        s = torch.unsqueeze(torch.tensor(s, dtype=torch.float), 0).to(self.device)
        a = self.actor(s).data.cpu().numpy().flatten()
        return a

    def learn(self, relay_buffer):
        batch_s, batch_a, batch_r, batch_s_, batch_dw = relay_buffer.sample(self.batch_size)  # Sample a batch

        batch_s = batch_s.to(self.device)
        batch_a = batch_a.to(self.device)
        batch_r = batch_r.to(self.device)
        batch_s_ = batch_s_.to(self.device)
        batch_dw = batch_dw.to(self.device)

        # Compute the target Q
        with torch.no_grad():  # target_Q has no gradient
            Q_ = self.critic_target(batch_s_, self.actor_target(batch_s_))
            target_Q = batch_r + self.GAMMA * (1 - batch_dw) * Q_

        # Compute the current Q and the critic loss
        current_Q = self.critic(batch_s, batch_a)
        critic_loss = self.MseLoss(target_Q, current_Q)
        # Optimize the critic
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # Freeze critic networks so you don't waste computational effort
        for params in self.critic.parameters():
            params.requires_grad = False

        # Compute the actor loss
        actor_loss = -self.critic(batch_s, self.actor(batch_s)).mean()
        # Optimize the actor
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        # Unfreeze critic networks
        for params in self.critic.parameters():
            params.requires_grad = True

        # Softly update the target networks
        for param, target_param in zip(self.critic.parameters(), self.critic_target.parameters()):
            target_param.data.copy_(self.TAU * param.data + (1 - self.TAU) * target_param.data)

        for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
            target_param.data.copy_(self.TAU * param.data + (1 - self.TAU) * target_param.data)

def reward_adapter(r):
    r = (r + 8) / 8
    return r

def evaluate_policy(env, agent):
    times = 3  # Perform three evaluations and calculate the average
    evaluate_reward = 0
    for _ in range(times):
        s,_ = env.reset()
        old_s = s
        done = False
        episode_reward = 0
        while not done:
            a = agent.choose_action(s)  # We do not add noise when evaluating
            s_, r, done, _ = env.step(a)
            episode_reward += r
            s = s_
        evaluate_reward += episode_reward
        print('------'*10)
        print('State:', np.round(old_s[0],5), old_s[1].astype(int))
        print('Action:', a)
        print('Next_observation:', np.round(s_[0],5), s_[1].astype(int))
        print('Reward:', r)
        print('------'*10)

    return int(evaluate_reward / times)

# def wandb_init(config: dict) -> None:
#     wandb.init(
#         project=config["project"],
#         group=config["group"],
#         name=config["name"],
#     )
#     wandb.run.save()

if __name__ == '__main__':
    # Wandb logging
    project: str = "CannonBall-env"
    group: str = "CannonBall_DDPG"
    name: str = "RUN_1"



    env_name = ['gym_CannonBall/CannonEnv-v0']
    env_index = 0
    env = gym.make(env_name[env_index])
    env_evaluate = gym.make(env_name[env_index])  # When evaluating the policy, we need to rebuild an environment
    number = 1
    # Set random seed
    seed = 0
    env.seed(seed)
    env.action_space.seed(seed)
    env_evaluate.seed(seed)
    env_evaluate.action_space.seed(seed)
    #np.random.seed(seed)
    torch.manual_seed(seed)

    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    max_action = float(env.action_space.high[0])
    max_episode_steps = 1  # Maximum number of steps per episode
    print("env={}".format(env_name[env_index]))
    print("state_dim={}".format(state_dim))
    print("action_dim={}".format(action_dim))
    print("max_action={}".format(max_action))
    print("max_episode_steps={}".format(max_episode_steps))

    agent = DDPG(state_dim, action_dim, max_action)
    replay_buffer = ReplayBuffer(state_dim, action_dim)
    # Build a tensorboard
    num = int(np.random.random()*100)
    writer = SummaryWriter(log_dir='runs/DDPG/DDPG_env_{}_number_{}'.format(env_name[env_index], num, seed))

    noise_std = 0.1 * max_action  # the std of Gaussian noise for exploration
    max_train_steps = 3e6  # Maximum number of training steps
    random_steps = 25e3  # Take the random actions in the beginning for the better exploration
    update_freq = 50  # Take 50 steps,then update the networks 50 times
    evaluate_freq = 1e3  # Evaluate the policy every 'evaluate_freq' steps
    evaluate_num = 0  # Record the number of evaluations
    evaluate_rewards = []  # Record the rewards during the evaluating
    total_steps = 0  # Record the total steps during the training

    while total_steps < max_train_steps:
        s, _ = env.reset()
        episode_steps = 0
        done = False
        while not done:
            episode_steps += 1
            if total_steps < random_steps:  # Take the random actions in the beginning for the better exploration
                a = env.action_space.sample()
            else:
                # Add Gaussian noise to actions for exploration
                a = agent.choose_action(s)
                a = (a + np.random.normal(0, noise_std, size=action_dim)).clip(-max_action, max_action)
            s_, r, done, _ = env.step(a)
            r = reward_adapter(r)
            if done and episode_steps != max_episode_steps:
                dw = True
            else:
                dw = False
            replay_buffer.store(s, a, r, s_, dw)  # Store the transition
            s = s_

            # Take 50 steps,then update the networks 50 times
            if total_steps >= random_steps and total_steps % update_freq == 0:
                for _ in range(update_freq):
                    agent.learn(replay_buffer)

            # Evaluate the policy every 'evaluate_freq' steps
            if (total_steps + 1) % evaluate_freq == 0:
                evaluate_num += 1
                evaluate_reward = evaluate_policy(env_evaluate, agent)
                evaluate_rewards.append(evaluate_reward)
                print("evaluate_num:{} \t evaluate_reward:{}".format(evaluate_num, evaluate_reward))
                writer.add_scalar('Reward for episode_{}'.format(env_name[env_index]), evaluate_reward, global_step=total_steps)
                # writer.add_scalar('Reward for episode 3 episodes', evaluate_reward/3,global_step=total_steps)
                # Save the rewards
                # if evaluate_num % 10 == 0:
                    # print('------'*10)
                    # print('State:', np.round(info['observation'][0],5), info['observation'][1].astype(int))
                    # print('Action:', info['action'])
                    # print('Next_observation:', np.round(info['next_observation'],3).astype(int))
                    # print('Reward:', info['reward'])
                    # print('------'*10)
                    # np.save('./data_train/DDPG_env_{}_number_{}_seed_{}.npy'.format(env_name[env_index], number, seed), np.array(evaluate_rewards))
                    # print("REWARDS:", np.array(evaluate_rewards))

            total_steps += 1
