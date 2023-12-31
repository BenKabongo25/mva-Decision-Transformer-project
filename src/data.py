# Deep Learning
# January 2024
#
# Ben Kabongo
# M2 MVA, ENS Paris-Saclay


import json
import numpy as np
import os
import warnings
from tqdm import tqdm
warnings.filterwarnings(action="ignore")

from mini_rl_lib.mdp_factory import MDPFactory
from mini_rl_lib.enums import MDPTransitionType, MDPRewardType, PolicyType


def create(
    n_states,
    n_actions,
    n_rewards=2,
    transition_function_type=MDPTransitionType.SA_DETERMINISTIC,
    reward_function_type=MDPRewardType.SA,
    p=0.1,
    gamma=0.99,
    eps=1e-3,
    alpha=1e-3,
    policy_type=PolicyType.VI,
    train_n_episodes=100,
    n_replay=100,
    max_step=100,
    random_play_p=0.1,
    seed=42,
    verbose=True,
    base_dir=".",
    data_dir_name=None
):

    if data_dir_name is None:
        data_dir_name = (f"S{n_states}_A{n_actions}_R{n_rewards}" 
                      + f"_T{transition_function_type.value}_R{reward_function_type.value}")

    data_dir = (f"{base_dir}/{data_dir_name}/")
    os.makedirs(data_dir, exist_ok=True)

    factory = MDPFactory(
        transition_function_type=transition_function_type,
        reward_function_type=reward_function_type,
        n_states=n_states,
        n_actions=n_actions,
        n_rewards=n_rewards,
        p=p,
        gamma=gamma,
        eps=eps,
        alpha=alpha,
        policy_type=policy_type
    )

    factory.train_policy(n_epidoes=train_n_episodes)
    policy = factory.policy.get_policy()
    
    target_return = 0.
    state, info = factory.model.reset(seed=seed)
    if verbose:
        print("Policy expert-level")
        print(". =>", state, None, False, False, info)
    for _ in range(max_step):
        action = policy[state]
        state, reward, terminated, truncated, info = factory.model.step(action)
        target_return += float(reward)
        if verbose:
            print(action, "=>", state, reward, terminated, truncated, info)
        if terminated or truncated:
            break

    data_min_step = max_step
    data_max_step = 0

    data = []
    for i in range(n_replay):
        states  = []
        actions = []
        rewards = []
        times   = []

        state, info = factory.model.reset(seed=seed)
        state = factory.model._current_state
        if verbose:
            print(f"\n{'='*100}\nPlay {i}")
            print(". =>", state, None, False, False, info)

        for t in range(max_step):
            player = "policy"
            if np.random.random() < random_play_p:
                player = "random"
                action = factory.model.action_space.sample()
            else:
                action = policy[state]   
            next_state, reward, terminated, truncated, info = factory.model.step(action)
            states.append(int(state))
            actions.append(int(action))
            rewards.append(float(reward))
            times.append(int(t))
            state = next_state

            if verbose:
                print(f"[{player}]", action, "=>", next_state, reward, terminated, truncated, info)
            if terminated or truncated:
                break
        
        if t < data_min_step:
            data_min_step = t
        if t > data_max_step:
            data_max_step = t

        item = [states, actions, rewards, times]
        data.append(item)
    
    metadata = {
        "n_states": n_states,
        "n_actions": n_actions,
        "n_rewards": n_rewards,
        "target_return": target_return,
        "data_min_step": data_min_step,
        "data_max_step": data_max_step,
        "terminate_state_p": p,
        "random_play_p": random_play_p,
        "n_replay": n_replay
    }

    factory.save(data_dir + "model.json")
    with open(data_dir + "metadata.json", "w") as file:
        json.dump(metadata, file)
    with open(data_dir + "data.json", "w") as file:
        json.dump(data, file)


def load(data_dir):
    factory = MDPFactory.load(data_dir + "model.json")
    with open(data_dir + "metadata.json", "r") as file:
        metadata = json.load(file)
    with open(data_dir + "data.json", "r") as file:
        data = json.load(file)
    return factory, metadata, data


if __name__ == "__main__":
    for n_states in tqdm([10, 100, 1_000, 10_000, 10_000, 100_000, 1_000_000], "S"):
        print("States :", n_states)
        for n_actions in [2, 3, 4, 5, 10, 20, 50, 100]:
            print("Actions :", n_actions)
            for n_rewards in [2, 3, 4, 5, 10]:
                create(n_states, n_actions, n_rewards, 
                        p=(n_states/1_000_000_000), n_replay=10_000, max_step=1_000, 
                        random_play_p=0.5, verbose=False,
                        base_dir="Project/mva-Decision-Transformer-project/data/mdp",
                )
