"""
Task definitions and grading functions.
Each task represents a specific incident scenario with deterministic evaluation.
"""

from typing import Dict, List, Callable
from models import SystemState, EpisodeInfo


class Task:
    """Base task definition."""
    
    def __init__(
        self,
        name: str,
        description: str,
        incident_type: str,
        optimal_steps: int,
        optimal_actions: List[str]
    ):
        self.name = name
        self.description = description
        self.incident_type = incident_type
        self.optimal_steps = optimal_steps
        self.optimal_actions = optimal_actions
    
    def grade(self, state: SystemState, actions_taken: List[str]) -> float:
        """
        Grade the episode performance.
        Returns score in [0.0, 1.0].
        """
        # Correctness (60%): Did agent resolve incident?
        correctness_score = 1.0 if state.is_resolved else 0.0
        
        # Efficiency (30%): Steps taken vs optimal
        if state.is_resolved:
            efficiency_score = max(0.0, 1.0 - (state.steps_taken - self.optimal_steps) / 10.0)
        else:
            efficiency_score = 0.0
        
        # Safety (10%): Avoided harmful actions
        safety_score = max(0.0, 1.0 - state.harmful_actions_count * 0.3)
        
        # Weighted combination
        total_score = (
            0.6 * correctness_score +
            0.3 * efficiency_score +
            0.1 * safety_score
        )
        
        return max(0.0, min(1.0, total_score))
    
    def check_diagnosis(self, actions_taken: List[str]) -> bool:
        """Check if agent performed correct diagnostic actions."""
        diagnostic_actions = ["inspect_logs", "check_metrics"]
        return any(action in actions_taken for action in diagnostic_actions)


# Task 1: EASY - Simple service crash
TASK_EASY = Task(
    name="easy",
    description="API service crashed due to out-of-memory error. Clear logs, single-step fix.",
    incident_type="api_crash",
    optimal_steps=2,
    optimal_actions=["inspect_logs", "restart_service:api"]
)


# Task 2: MEDIUM - Database connection pool exhaustion
TASK_MEDIUM = Task(
    name="medium",
    description="Database connection pool exhausted causing API timeouts. Requires diagnosis and patch.",
    incident_type="db_connection_exhaustion",
    optimal_steps=3,
    optimal_actions=["inspect_logs", "check_metrics", "apply_patch:database"]
)


# Task 3: HARD - Cascading failure from cache invalidation storm
TASK_HARD = Task(
    name="hard",
    description="Bad deployment caused cache invalidation storm leading to DB overload and API degradation. Multi-step resolution required.",
    incident_type="cache_failure_cascade",
    optimal_steps=4,
    optimal_actions=["inspect_logs", "restart_service:cache", "scale_service:database", "rollback_deployment:api"]
)


TASKS = {
    "easy": TASK_EASY,
    "medium": TASK_MEDIUM,
    "hard": TASK_HARD
}


def grade_episode(task: Task, state: SystemState) -> EpisodeInfo:
    """
    Deterministic grading function for an episode.
    
    Args:
        task: The task definition
        state: Final system state
    
    Returns:
        EpisodeInfo with detailed scoring
    """
    score = task.grade(state, state.actions_history)
    
    return EpisodeInfo(
        success=state.is_resolved,
        score=score,
        steps_taken=state.steps_taken,
        optimal_steps=task.optimal_steps,
        root_cause=state.root_cause,
        diagnosis_correct=task.check_diagnosis(state.actions_history),
        harmful_actions=state.harmful_actions_count
    )


def get_task(task_name: str) -> Task:
    """Get task by name."""
    if task_name not in TASKS:
        raise ValueError(f"Unknown task: {task_name}. Available: {list(TASKS.keys())}")
    return TASKS[task_name]
