"""
Example usage of the Production Incident Response Simulator.
Demonstrates basic environment interaction and custom agent implementation.
"""

from env import ProductionIncidentEnv
from models import Action
import random


def random_agent_example():
    """Example: Random agent (baseline comparison)."""
    print("="*60)
    print("Example 1: Random Agent")
    print("="*60)
    
    env = ProductionIncidentEnv(task="easy", seed=42)
    obs = env.reset()
    
    done = False
    total_reward = 0
    
    while not done:
        # Random action selection
        action_type = random.choice([
            "restart_service", "inspect_logs", "check_metrics", 
            "apply_patch", "do_nothing"
        ])
        target = random.choice(["api", "database", "cache", "queue"])
        
        action = Action(action_type=action_type, target=target)
        obs, reward, done, info = env.step(action)
        
        total_reward += reward.total
        print(f"Step {obs.time_elapsed}: {action_type} -> {target} | Reward: {reward.total:+.2f}")
    
    print(f"\nEpisode finished!")
    print(f"Total Reward: {total_reward:.2f}")
    print(f"Score: {info.get('score', 0.0):.3f}")
    print(f"Success: {info['episode']['success']}\n")


def rule_based_agent_example():
    """Example: Simple rule-based agent."""
    print("="*60)
    print("Example 2: Rule-Based Agent")
    print("="*60)
    
    env = ProductionIncidentEnv(task="medium", seed=42)
    obs = env.reset()
    
    done = False
    diagnosed = False
    
    while not done:
        # Simple rule-based logic
        if not diagnosed:
            # First, diagnose
            action = Action(action_type="inspect_logs")
            diagnosed = True
        elif "DB_CONNECTION" in " ".join(obs.alerts):
            # Connection pool issue
            action = Action(action_type="apply_patch", target="database")
        elif "HIGH_DB_CPU" in " ".join(obs.alerts):
            action = Action(action_type="scale_service", target="database")
        elif "API_SERVICE_DOWN" in " ".join(obs.alerts):
            action = Action(action_type="restart_service", target="api")
        elif "CACHE_SERVICE_DOWN" in " ".join(obs.alerts):
            action = Action(action_type="restart_service", target="cache")
        else:
            action = Action(action_type="check_metrics")
        
        obs, reward, done, info = env.step(action)
        print(f"Step {obs.time_elapsed}: {action.action_type} | Reward: {reward.total:+.2f}")
    
    print(f"\nEpisode finished!")
    print(f"Score: {info.get('score', 0.0):.3f}")
    print(f"Success: {info['episode']['success']}\n")


def state_inspection_example():
    """Example: Inspecting internal state for debugging."""
    print("="*60)
    print("Example 3: State Inspection")
    print("="*60)
    
    env = ProductionIncidentEnv(task="hard", seed=42)
    obs = env.reset()
    
    # Get internal state (for debugging/analysis)
    state = env.state()
    
    print(f"Task: {env._current_task.name}")
    print(f"Root Cause (hidden): {state.root_cause}")
    print(f"Incident Type: {state.incident_type}")
    print(f"\nService Status:")
    print(f"  API: {state.api_status}")
    print(f"  Database: {state.db_status}")
    print(f"  Cache: {state.cache_status}")
    print(f"  Queue: {state.queue_status}")
    print(f"\nActive Alerts: {obs.alerts}")
    print(f"\nOptimal Solution: {env._current_task.optimal_steps} steps")
    print()


def multi_episode_evaluation():
    """Example: Evaluate agent over multiple episodes."""
    print("="*60)
    print("Example 4: Multi-Episode Evaluation")
    print("="*60)
    
    results = []
    
    for episode in range(3):
        env = ProductionIncidentEnv(task="easy", seed=episode)
        obs = env.reset()
        
        done = False
        while not done:
            # Simple heuristic agent
            if obs.time_elapsed == 0:
                action = Action(action_type="inspect_logs")
            elif "API_SERVICE_DOWN" in " ".join(obs.alerts):
                action = Action(action_type="restart_service", target="api")
            else:
                action = Action(action_type="check_metrics")
            
            obs, reward, done, info = env.step(action)
        
        results.append(info["episode"])
        print(f"Episode {episode + 1}: Score={info['score']:.3f}, Success={info['episode']['success']}")
    
    avg_score = sum(r["score"] for r in results) / len(results)
    success_rate = sum(1 for r in results if r["success"]) / len(results)
    
    print(f"\nAverage Score: {avg_score:.3f}")
    print(f"Success Rate: {success_rate:.1%}\n")


if __name__ == "__main__":
    random_agent_example()
    rule_based_agent_example()
    state_inspection_example()
    multi_episode_evaluation()
