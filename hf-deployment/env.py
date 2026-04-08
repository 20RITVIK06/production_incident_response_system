"""
Production Incident Response Simulator - Main Environment.
OpenEnv-compatible RL environment for training agents on incident response.
"""

from typing import Dict, Tuple, Optional, Any, List
import random
from models import Observation, Action, Reward, SystemState, Metrics, EpisodeInfo
from system_simulator import MicroserviceSystem
from tasks import get_task, grade_episode, TASKS, Task, TASK_EASY, TASK_MEDIUM, TASK_HARD


# Action space definition
ACTION_SPACE = [
    "restart_service",
    "scale_service", 
    "rollback_deployment",
    "inspect_logs",
    "check_metrics",
    "apply_patch",
    "do_nothing"
]

VALID_TARGETS = ["api", "database", "cache", "queue"]


class ProductionIncidentEnv:
    """
    OpenEnv-compatible environment simulating production incident response.
    
    Agent must diagnose and resolve incidents in a microservices system
    with partial observability and realistic noise.
    """
    
    def __init__(
        self,
        task: str = "easy",
        max_steps: int = 20,
        noise_level: float = 0.2,
        seed: Optional[int] = None
    ):
        """
        Initialize environment.
        
        Args:
            task: Task difficulty ("easy", "medium", "hard", or "random")
            max_steps: Maximum steps before episode termination
            noise_level: Amount of noise in observations [0, 1]
            seed: Random seed for reproducibility
        """
        if task not in TASKS and task != "random":
            raise ValueError(f"Invalid task: {task}. Choose from {list(TASKS.keys())} or 'random'")
        
        self.task_name = task
        self.max_steps = max_steps
        self.noise_level = noise_level
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Initialize system simulator
        self.system = MicroserviceSystem(seed=seed)
        
        # Episode state
        self._state: Optional[SystemState] = None
        self._current_task = None
        self._episode_reward = 0.0
    
    def reset(self) -> Observation:
        """
        Reset environment to initial state and start new episode.
        
        Returns:
            Initial observation
        """
        # Select task
        if self.task_name == "random":
            task_name = self.rng.choice(list(TASKS.keys()))
            self._current_task = get_task(task_name)
        else:
            self._current_task = get_task(self.task_name)
        
        # Reset system
        self.system.reset()
        self.system.inject_incident(self._current_task.incident_type)
        
        # Initialize state
        self._state = SystemState(
            api_status=self.system.api_status,
            db_status=self.system.db_status,
            cache_status=self.system.cache_status,
            queue_status=self.system.queue_status,
            root_cause=self.system.root_cause,
            incident_type=self.system.incident_type,
            is_resolved=False,
            diagnosis_correct=False,
            true_metrics=self.system.get_metrics(add_noise=False),
            steps_taken=0,
            actions_history=[],
            harmful_actions_count=0
        )
        
        self._episode_reward = 0.0
        
        # Return initial observation
        return self._get_observation()
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute action and return result.
        
        Args:
            action: Action to take
        
        Returns:
            observation: New observation
            reward: Reward for this step
            done: Whether episode is complete
            info: Additional information
        """
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        # Parse action
        action_type = action.action_type
        target = action.target or "api"
        
        # Record action
        action_str = f"{action_type}:{target}" if target else action_type
        self._state.actions_history.append(action_str)
        self._state.steps_taken += 1
        
        # Apply action to system
        success, message = self.system.apply_action(action_type, target)
        
        # Calculate reward
        reward = self._calculate_reward(action_type, target, success)
        
        # Update state
        self._state.api_status = self.system.api_status
        self._state.db_status = self.system.db_status
        self._state.cache_status = self.system.cache_status
        self._state.queue_status = self.system.queue_status
        self._state.is_resolved = not self.system.incident_active
        self._state.true_metrics = self.system.get_metrics(add_noise=False)
        
        # Check diagnosis
        if action_type in ["inspect_logs", "check_metrics"]:
            if self._is_correct_diagnosis(action_type):
                self._state.diagnosis_correct = True
        
        # Simulate time passing
        self.system.simulate_time_step()
        
        # Check termination
        done = self._check_done()
        
        # Build info dict
        info = {
            "message": message,
            "system_healthy": self.system.is_system_healthy(),
            "root_cause": self._state.root_cause if done else None
        }
        
        # Add episode info if done
        if done:
            episode_info = grade_episode(self._current_task, self._state)
            info["episode"] = episode_info.model_dump()
            info["score"] = episode_info.score
        
        self._episode_reward += reward.total
        
        return self._get_observation(action_type), reward, done, info
    
    def state(self) -> SystemState:
        """
        Return complete internal state (for debugging/analysis).
        
        Returns:
            Full system state
        """
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._state.model_copy(deep=True)
    
    def _get_observation(self, last_action: Optional[str] = None) -> Observation:
        """Generate observation with partial observability and noise."""
        logs = self.system.get_logs(last_action)
        metrics = self.system.get_metrics(add_noise=True)
        alerts = self.system.get_alerts()
        
        # Add noise to logs (random irrelevant entries)
        if self.rng.random() < self.noise_level:
            noise_logs = [
                "[INFO] Cron: Backup job completed successfully",
                "[DEBUG] API: Request processed in 45ms",
                "[INFO] Monitoring: Heartbeat sent"
            ]
            logs += "\n" + self.rng.choice(noise_logs)
        
        return Observation(
            logs=logs,
            metrics=metrics,
            alerts=alerts,
            time_elapsed=self._state.steps_taken,
            previous_action=self._state.actions_history[-1] if self._state.actions_history else None
        )
    
    def _calculate_reward(self, action_type: str, target: str, success: bool) -> Reward:
        """Calculate reward for action taken."""
        correctness = 0.0
        efficiency = -0.05  # Time penalty
        safety = 0.0
        progress = 0.0
        
        # Check if action is correct for current incident
        if self._state.is_resolved:
            # Incident resolved
            correctness = 1.0
            progress = 0.5
        elif self._is_correct_action(action_type, target):
            correctness = 0.2
            progress = 0.1
        elif self._is_harmful_action(action_type, target):
            safety = -0.3
            self._state.harmful_actions_count += 1
        elif action_type == "do_nothing":
            efficiency = -0.1
        else:
            # Neutral or slightly negative
            correctness = -0.1
        
        total = correctness + efficiency + safety + progress
        
        return Reward(
            total=total,
            correctness=correctness,
            efficiency=efficiency,
            safety=safety,
            progress=progress
        )
    
    def _is_correct_action(self, action_type: str, target: str) -> bool:
        """Check if action is correct for current incident."""
        root_cause = self._state.root_cause
        
        if root_cause == "api_out_of_memory":
            return action_type == "restart_service" and target == "api"
        
        elif root_cause == "database_connection_pool_exhausted":
            return (
                (action_type == "apply_patch" and target == "database") or
                (action_type == "inspect_logs") or
                (action_type == "check_metrics")
            )
        
        elif root_cause == "cache_invalidation_storm":
            # Multi-step solution
            if self.system.cache_status == "down":
                return action_type == "restart_service" and target == "cache"
            elif self.system.db_status == "degraded" and self.system.cache_status == "healthy":
                return action_type == "scale_service" and target == "database"
            elif self.system.api_status == "degraded":
                return action_type == "rollback_deployment" and target == "api"
        
        # Diagnostic actions are always useful
        if action_type in ["inspect_logs", "check_metrics"]:
            return True
        
        return False
    
    def _is_harmful_action(self, action_type: str, target: str) -> bool:
        """Check if action could make things worse."""
        # Restarting healthy services is harmful
        if action_type == "restart_service":
            if target == "api" and self.system.api_status == "healthy":
                return True
            if target == "database" and self.system.db_status == "healthy":
                return True
        
        # Scaling when not needed wastes resources
        if action_type == "scale_service" and self.system.is_system_healthy():
            return True
        
        # Rollback when not a deployment issue
        if action_type == "rollback_deployment" and "deployment" not in self._state.root_cause:
            if self._state.steps_taken > 2:  # Only harmful if done without diagnosis
                return True
        
        return False
    
    def _is_correct_diagnosis(self, action_type: str) -> bool:
        """Check if diagnostic action revealed root cause."""
        if action_type == "inspect_logs":
            # Logs reveal root cause for most incidents
            return True
        elif action_type == "check_metrics":
            # Metrics help with resource issues
            return "exhaustion" in self._state.root_cause or "memory" in self._state.root_cause
        return False
    
    def _check_done(self) -> bool:
        """Check if episode should terminate."""
        # Success condition
        if self._state.is_resolved and self.system.is_system_healthy():
            return True
        
        # Failure conditions
        if self._state.steps_taken >= self.max_steps:
            return True
        
        if self._state.harmful_actions_count >= 3:
            return True
        
        return False


def get_all_tasks() -> Dict[str, Task]:
    """Return all available tasks."""
    return {
        "easy": TASK_EASY,
        "medium": TASK_MEDIUM,
        "hard": TASK_HARD
    }
