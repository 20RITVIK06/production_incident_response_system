"""
Baseline agent using OpenAI API.
Runs agent through all tasks and outputs reproducible scores.
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from env import ProductionIncidentEnv, ACTION_SPACE, VALID_TARGETS
from models import Action


class BaselineAgent:
    """GPT-4 powered baseline agent for incident response."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.0):
        """
        Initialize baseline agent.
        
        Args:
            model: OpenAI model to use
            temperature: Sampling temperature (0 for deterministic)
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.conversation_history = []
    
    def reset(self):
        """Reset conversation history for new episode."""
        self.conversation_history = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
    
    def select_action(self, observation: Dict) -> Action:
        """
        Select action based on observation using LLM.
        
        Args:
            observation: Current observation dict
        
        Returns:
            Action to take
        """
        # Format observation for LLM
        obs_text = self._format_observation(observation)
        
        self.conversation_history.append({
            "role": "user",
            "content": obs_text
        })
        
        # Get LLM response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=self.temperature,
            max_tokens=150
        )
        
        response_text = response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        # Parse action from response
        action = self._parse_action(response_text)
        return action
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        return f"""You are a senior DevOps engineer responding to a production incident.

Your goal: Diagnose and resolve the incident as quickly as possible.

Available actions:
{', '.join(ACTION_SPACE)}

Valid targets: {', '.join(VALID_TARGETS)}

You will receive observations with logs, metrics, and alerts.
Respond with ONLY a JSON object in this format:
{{"action_type": "action_name", "target": "service_name"}}

For actions that don't need a target (inspect_logs, check_metrics, do_nothing), omit the target field.

Examples:
{{"action_type": "restart_service", "target": "api"}}
{{"action_type": "inspect_logs"}}
{{"action_type": "apply_patch", "target": "database"}}

Be strategic:
1. Diagnose before acting (inspect_logs, check_metrics)
2. Target root cause, not symptoms
3. Avoid unnecessary restarts
4. Work efficiently - time matters

Respond with ONLY the JSON action, no explanation."""
    
    def _format_observation(self, obs: Dict) -> str:
        """Format observation for LLM consumption."""
        return f"""
=== INCIDENT OBSERVATION ===

LOGS:
{obs['logs']}

METRICS:
- API: CPU={obs['metrics']['api_cpu']:.1f}%, Latency={obs['metrics']['api_latency']:.0f}ms, Memory={obs['metrics']['api_memory']:.1f}%
- Database: CPU={obs['metrics']['db_cpu']:.1f}%, Connections={obs['metrics']['db_connections']}, QueryTime={obs['metrics']['db_query_time']:.0f}ms
- Cache: HitRate={obs['metrics']['cache_hit_rate']:.2f}, Memory={obs['metrics']['cache_memory']:.1f}%
- Queue: Depth={obs['metrics']['queue_depth']}
- Errors: {obs['metrics']['error_rate']:.1f}/sec

ALERTS:
{chr(10).join('- ' + alert for alert in obs['alerts']) if obs['alerts'] else '- No active alerts'}

TIME ELAPSED: {obs['time_elapsed']} steps
PREVIOUS ACTION: {obs['previous_action'] or 'None'}

What action do you take?
"""
    
    def _parse_action(self, response: str) -> Action:
        """Parse action from LLM response."""
        try:
            # Extract JSON from response
            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            action_dict = json.loads(response)
            
            # Validate action type
            if action_dict["action_type"] not in ACTION_SPACE:
                print(f"Invalid action type: {action_dict['action_type']}, defaulting to do_nothing")
                return Action(action_type="do_nothing")
            
            # Validate target if present
            if "target" in action_dict and action_dict["target"] not in VALID_TARGETS:
                print(f"Invalid target: {action_dict['target']}, defaulting to api")
                action_dict["target"] = "api"
            
            return Action(**action_dict)
        
        except Exception as e:
            print(f"Failed to parse action: {e}")
            print(f"Response: {response}")
            return Action(action_type="do_nothing")


def run_episode(env: ProductionIncidentEnv, agent: BaselineAgent, verbose: bool = True) -> Dict:
    """Run a single episode."""
    agent.reset()
    obs = env.reset()
    
    done = False
    episode_rewards = []
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Starting episode: {env._current_task.name}")
        print(f"{'='*60}\n")
    
    step_count = 0
    while not done:
        # Agent selects action
        action = agent.select_action(obs.model_dump())
        
        if verbose:
            print(f"Step {step_count + 1}: {action.action_type}" + 
                  (f" -> {action.target}" if action.target else ""))
        
        # Environment step
        obs, reward, done, info = env.step(action)
        episode_rewards.append(reward.total)
        
        if verbose:
            print(f"  Reward: {reward.total:+.2f} | {info.get('message', '')}")
        
        step_count += 1
    
    # Episode complete
    episode_info = info.get("episode", {})
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Episode Complete!")
        print(f"  Success: {episode_info.get('success', False)}")
        print(f"  Score: {episode_info.get('score', 0.0):.3f}")
        print(f"  Steps: {episode_info.get('steps_taken', 0)} (optimal: {episode_info.get('optimal_steps', 0)})")
        print(f"  Root Cause: {episode_info.get('root_cause', 'unknown')}")
        print(f"  Diagnosis Correct: {episode_info.get('diagnosis_correct', False)}")
        print(f"{'='*60}\n")
    
    return episode_info


def run_baseline(num_episodes: int = 5, task: Optional[str] = None):
    """
    Run baseline agent on all tasks.
    
    Args:
        num_episodes: Number of episodes per task
        task: Specific task to run (None = all tasks)
    """
    agent = BaselineAgent(model="gpt-4", temperature=0.0)
    
    tasks_to_run = [task] if task else ["easy", "medium", "hard"]
    
    results = {}
    
    for task_name in tasks_to_run:
        print(f"\n{'#'*60}")
        print(f"# Running Task: {task_name.upper()}")
        print(f"{'#'*60}")
        
        task_results = []
        
        for episode_num in range(num_episodes):
            print(f"\n--- Episode {episode_num + 1}/{num_episodes} ---")
            
            env = ProductionIncidentEnv(task=task_name, seed=episode_num)
            episode_info = run_episode(env, agent, verbose=True)
            task_results.append(episode_info)
        
        # Aggregate results
        success_rate = sum(1 for r in task_results if r["success"]) / num_episodes
        avg_score = sum(r["score"] for r in task_results) / num_episodes
        avg_steps = sum(r["steps_taken"] for r in task_results) / num_episodes
        
        results[task_name] = {
            "success_rate": success_rate,
            "average_score": avg_score,
            "average_steps": avg_steps,
            "episodes": task_results
        }
        
        print(f"\n{'='*60}")
        print(f"Task: {task_name.upper()} - Summary")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Average Score: {avg_score:.3f}")
        print(f"  Average Steps: {avg_steps:.1f}")
        print(f"{'='*60}")
    
    # Save results
    with open("baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to baseline_results.json")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run baseline agent on incident response tasks")
    parser.add_argument("--task", type=str, default=None, 
                       choices=["easy", "medium", "hard"],
                       help="Specific task to run (default: all tasks)")
    parser.add_argument("--episodes", type=int, default=5,
                       help="Number of episodes per task")
    
    args = parser.parse_args()
    
    run_baseline(num_episodes=args.episodes, task=args.task)
