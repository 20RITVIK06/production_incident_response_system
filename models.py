"""
Pydantic models for OpenEnv compatibility.
Defines typed Observation, Action, and Reward structures.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Metrics(BaseModel):
    """System metrics snapshot."""
    api_cpu: float = Field(ge=0, le=100, description="API CPU usage percentage")
    api_latency: float = Field(ge=0, description="API latency in milliseconds")
    api_memory: float = Field(ge=0, le=100, description="API memory usage percentage")
    db_cpu: float = Field(ge=0, le=100, description="Database CPU usage")
    db_connections: int = Field(ge=0, description="Active DB connections")
    db_query_time: float = Field(ge=0, description="Average query time in ms")
    cache_hit_rate: float = Field(ge=0, le=1, description="Cache hit rate")
    cache_memory: float = Field(ge=0, le=100, description="Cache memory usage")
    queue_depth: int = Field(ge=0, description="Message queue depth")
    error_rate: float = Field(ge=0, description="Errors per second")


class Observation(BaseModel):
    """
    Agent observation of the system state.
    Partial observability with noise.
    """
    logs: str = Field(description="Recent log entries from all services")
    metrics: Metrics = Field(description="Current system metrics")
    alerts: List[str] = Field(default_factory=list, description="Active alerts")
    time_elapsed: int = Field(ge=0, description="Steps taken in episode")
    previous_action: Optional[str] = Field(default=None, description="Last action taken")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "logs": "[ERROR] API: Connection timeout to database\n[WARN] DB: High connection count",
                "metrics": {
                    "api_cpu": 45.2,
                    "api_latency": 1250.0,
                    "api_memory": 78.5,
                    "db_cpu": 92.3,
                    "db_connections": 95,
                    "db_query_time": 450.0,
                    "cache_hit_rate": 0.65,
                    "cache_memory": 55.0,
                    "queue_depth": 1200,
                    "error_rate": 15.3
                },
                "alerts": ["HIGH_DB_CPU", "API_LATENCY_SPIKE"],
                "time_elapsed": 3,
                "previous_action": "inspect_logs"
            }
        }
    )


class Action(BaseModel):
    """
    Agent action in the environment.
    Discrete action space with 7 possible interventions.
    """
    action_type: str = Field(
        description="Type of action to take",
        pattern="^(restart_service|scale_service|rollback_deployment|inspect_logs|check_metrics|apply_patch|do_nothing)$"
    )
    target: Optional[str] = Field(
        default=None,
        description="Target service (api, database, cache, queue)",
        pattern="^(api|database|cache|queue)?$"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action_type": "restart_service",
                "target": "api"
            }
        }
    )


class Reward(BaseModel):
    """
    Reward signal for the agent.
    Includes breakdown for interpretability.
    """
    total: float = Field(description="Total reward for this step")
    correctness: float = Field(default=0.0, description="Reward for correct action")
    efficiency: float = Field(default=0.0, description="Time penalty")
    safety: float = Field(default=0.0, description="Penalty for harmful actions")
    progress: float = Field(default=0.0, description="Progress toward resolution")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 0.15,
                "correctness": 0.2,
                "efficiency": -0.05,
                "safety": 0.0,
                "progress": 0.0
            }
        }
    )


class SystemState(BaseModel):
    """
    Complete internal state of the simulated system.
    Not directly observable by agent (partial observability).
    """
    # Service health
    api_status: str = Field(pattern="^(healthy|degraded|down)$")
    db_status: str = Field(pattern="^(healthy|degraded|down)$")
    cache_status: str = Field(pattern="^(healthy|degraded|down)$")
    queue_status: str = Field(pattern="^(healthy|degraded|down)$")
    
    # Root cause (hidden from agent)
    root_cause: str = Field(description="Actual root cause of incident")
    incident_type: str = Field(description="Type of incident")
    
    # Incident state
    is_resolved: bool = Field(default=False)
    diagnosis_correct: bool = Field(default=False)
    
    # Metrics (ground truth, before noise)
    true_metrics: Metrics
    
    # Episode tracking
    steps_taken: int = Field(default=0)
    actions_history: List[str] = Field(default_factory=list)
    harmful_actions_count: int = Field(default=0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_status": "degraded",
                "db_status": "degraded",
                "cache_status": "healthy",
                "queue_status": "healthy",
                "root_cause": "database_connection_pool_exhausted",
                "incident_type": "resource_exhaustion",
                "is_resolved": False,
                "diagnosis_correct": False,
                "true_metrics": {},
                "steps_taken": 2,
                "actions_history": ["inspect_logs", "check_metrics"],
                "harmful_actions_count": 0
            }
        }
    )


class EpisodeInfo(BaseModel):
    """
    Additional information returned at episode end.
    """
    success: bool = Field(description="Whether incident was resolved")
    score: float = Field(ge=0, le=1, description="Normalized score [0, 1]")
    steps_taken: int = Field(description="Total steps in episode")
    optimal_steps: int = Field(description="Optimal solution length")
    root_cause: str = Field(description="Actual root cause")
    diagnosis_correct: bool = Field(description="Whether agent diagnosed correctly")
    harmful_actions: int = Field(description="Number of harmful actions taken")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "score": 0.78,
                "steps_taken": 4,
                "optimal_steps": 3,
                "root_cause": "memory_leak",
                "diagnosis_correct": True,
                "harmful_actions": 0
            }
        }
    )
