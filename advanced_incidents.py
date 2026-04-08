"""
Advanced incident scenarios with randomization.
Extends the base environment with more complex failure modes.
"""

from typing import Dict, Optional
import random
from system_simulator import MicroserviceSystem
from env import ProductionIncidentEnv


class AdvancedIncidentSimulator(MicroserviceSystem):
    """Extended system simulator with additional incident types."""
    
    def inject_incident(self, incident_type: str):
        """Inject incident including advanced types."""
        # Handle base incident types
        if incident_type in ["api_crash", "db_connection_exhaustion", "cache_failure_cascade"]:
            super().inject_incident(incident_type)
            return
        
        # Advanced incident types
        self.incident_active = True
        self.incident_type = incident_type
        
        if incident_type == "memory_leak":
            self.root_cause = "api_memory_leak"
            self.api_status = "degraded"
            self.api_memory = 88.0
            self.api_cpu = 65.0
            self.api_latency = 800.0
            self.error_rate = 5.0
            
        elif incident_type == "db_deadlock":
            self.root_cause = "database_deadlock"
            self.db_status = "degraded"
            self.db_cpu = 45.0
            self.db_connections = 85
            self.db_query_time = 5000.0  # Very slow queries
            self.api_status = "degraded"
            self.api_latency = 4000.0
            self.error_rate = 8.0
            
        elif incident_type == "network_latency_spike":
            self.root_cause = "network_latency_spike"
            self.api_status = "degraded"
            self.db_status = "degraded"
            self.api_latency = 3000.0
            self.db_query_time = 1500.0
            self.error_rate = 15.0
            
        elif incident_type == "disk_space_exhaustion":
            self.root_cause = "disk_space_full"
            self.db_status = "down"
            self.db_cpu = 10.0
            self.queue_status = "degraded"
            self.queue_depth = 8000
            self.api_status = "degraded"
            self.error_rate = 20.0
            
        elif incident_type == "deployment_bug":
            self.root_cause = "bad_deployment_api"
            self.api_status = "degraded"
            self.api_cpu = 55.0
            self.api_latency = 1200.0
            self.error_rate = 18.0
    
    def get_logs(self, action_type: str = None) -> str:
        """Generate logs including advanced incident types."""
        # Get base logs
        base_logs = super().get_logs(action_type)
        
        timestamp_base = "2026-03-30T14:23:"
        additional_logs = []
        
        # Advanced incident-specific logs
        if self.root_cause == "api_memory_leak":
            additional_logs.append(f"{timestamp_base}40 [WARN] API: Memory usage increasing steadily")
            additional_logs.append(f"{timestamp_base}41 [ERROR] API: GC overhead limit exceeded")
            
        elif self.root_cause == "database_deadlock":
            additional_logs.append(f"{timestamp_base}42 [ERROR] DB: Deadlock detected")
            additional_logs.append(f"{timestamp_base}42 [ERROR] DB: Transaction rolled back")
            additional_logs.append(f"{timestamp_base}43 [WARN] DB: Lock wait timeout exceeded")
            
        elif self.root_cause == "network_latency_spike":
            additional_logs.append(f"{timestamp_base}44 [WARN] Network: High latency detected (500ms RTT)")
            additional_logs.append(f"{timestamp_base}45 [ERROR] API: Upstream timeout")
            
        elif self.root_cause == "disk_space_full":
            additional_logs.append(f"{timestamp_base}46 [CRITICAL] DB: No space left on device")
            additional_logs.append(f"{timestamp_base}46 [ERROR] DB: Cannot write to WAL")
            additional_logs.append(f"{timestamp_base}47 [ERROR] Queue: Failed to persist message")
            
        elif self.root_cause == "bad_deployment_api":
            additional_logs.append(f"{timestamp_base}48 [ERROR] API: NullPointerException in UserController.java:142")
            additional_logs.append(f"{timestamp_base}48 [WARN] API: Deployment v3.2.0 started 5 minutes ago")
            additional_logs.append(f"{timestamp_base}49 [ERROR] API: 500 Internal Server Error")
        
        if additional_logs:
            return base_logs + "\n" + "\n".join(additional_logs)
        
        return base_logs


def generate_random_incident_config(difficulty: str = "medium", seed: Optional[int] = None) -> Dict:
    """
    Generate a random incident configuration.
    
    Args:
        difficulty: "easy", "medium", or "hard"
        seed: Random seed for reproducibility
    
    Returns:
        Incident configuration dict
    """
    rng = random.Random(seed)
    
    if difficulty == "easy":
        incident_types = ["api_crash", "memory_leak"]
        max_steps = 15
        noise_level = 0.1
        
    elif difficulty == "medium":
        incident_types = ["db_connection_exhaustion", "network_latency_spike", "deployment_bug", "db_deadlock"]
        max_steps = 20
        noise_level = 0.3
        
    else:  # hard
        incident_types = ["cache_failure_cascade", "disk_space_exhaustion"]
        max_steps = 25
        noise_level = 0.5
    
    incident_type = rng.choice(incident_types)
    
    return {
        "incident_type": incident_type,
        "difficulty": difficulty,
        "max_steps": max_steps,
        "noise_level": noise_level,
        "cascading_failures": difficulty == "hard",
        "time_pressure": rng.uniform(0.8, 1.2)  # Multiplier for time penalties
    }


class ConfigurableIncidentEnv(ProductionIncidentEnv):
    """
    Extended environment with configurable difficulty and random incidents.
    """
    
    def __init__(
        self,
        task: str = "easy",
        max_steps: int = 20,
        noise_level: float = 0.2,
        seed: Optional[int] = None,
        cascading_prob: float = 0.3,
        random_incidents: bool = False
    ):
        """
        Initialize configurable environment.
        
        Args:
            task: Task difficulty
            max_steps: Maximum steps
            noise_level: Observation noise [0, 1]
            seed: Random seed
            cascading_prob: Probability of cascading failures
            random_incidents: Use random incident generator
        """
        super().__init__(task, max_steps, noise_level, seed)
        self.cascading_prob = cascading_prob
        self.random_incidents = random_incidents
        
        # Use advanced simulator
        self.system = AdvancedIncidentSimulator(seed=seed)
    
    def reset(self):
        """Reset with optional random incident generation."""
        if self.random_incidents:
            # Generate random incident
            config = generate_random_incident_config(
                difficulty=self.task_name if self.task_name != "random" else "medium",
                seed=self.seed
            )
            self.max_steps = config["max_steps"]
            self.noise_level = config["noise_level"]
        
        return super().reset()


if __name__ == "__main__":
    print("Advanced Incident Scenarios Demo\n")
    
    # Demo 1: Memory leak
    print("Scenario 1: Memory Leak")
    env = ConfigurableIncidentEnv(task="easy", random_incidents=False, seed=42)
    env.system.inject_incident("memory_leak")
    logs = env.system.get_logs()
    print(logs[:200] + "...\n")
    
    # Demo 2: Database deadlock
    print("Scenario 2: Database Deadlock")
    env.system.reset()
    env.system.inject_incident("db_deadlock")
    logs = env.system.get_logs()
    print(logs[:200] + "...\n")
    
    # Demo 3: Random incident generation
    print("Scenario 3: Random Incident (Hard)")
    config = generate_random_incident_config(difficulty="hard", seed=123)
    print(f"Generated: {config}\n")
