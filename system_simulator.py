"""
Microservices system simulator.
Simulates realistic service behavior, failures, and recovery.
"""

import random
from typing import Dict, List, Tuple, Optional
from models import Metrics


class MicroserviceSystem:
    """Simulates a production microservices system with realistic failure modes."""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.reset()
    
    def reset(self):
        """Reset system to healthy state."""
        self.api_status = "healthy"
        self.db_status = "healthy"
        self.cache_status = "healthy"
        self.queue_status = "healthy"
        
        self.api_cpu = 25.0
        self.api_latency = 50.0
        self.api_memory = 40.0
        
        self.db_cpu = 30.0
        self.db_connections = 20
        self.db_query_time = 15.0
        
        self.cache_hit_rate = 0.85
        self.cache_memory = 45.0
        
        self.queue_depth = 50
        self.error_rate = 0.1
        
        self.incident_active = False
        self.root_cause = None
        self.incident_type = None
    
    def inject_incident(self, incident_type: str):
        """Inject a specific incident into the system."""
        self.incident_active = True
        self.incident_type = incident_type
        
        if incident_type == "api_crash":
            self.root_cause = "api_out_of_memory"
            self.api_status = "down"
            self.api_cpu = 0.0
            self.api_memory = 95.0
            self.error_rate = 50.0
            
        elif incident_type == "db_connection_exhaustion":
            self.root_cause = "database_connection_pool_exhausted"
            self.db_status = "degraded"
            self.db_connections = 98  # Near limit of 100
            self.db_cpu = 85.0
            self.api_status = "degraded"
            self.api_latency = 2500.0
            self.error_rate = 12.0
            
        elif incident_type == "cache_failure_cascade":
            self.root_cause = "cache_invalidation_storm"
            self.cache_status = "down"
            self.cache_hit_rate = 0.0
            self.cache_memory = 98.0
            # Cascading effects
            self.db_status = "degraded"
            self.db_cpu = 95.0
            self.db_connections = 95
            self.api_status = "degraded"
            self.api_latency = 3500.0
            self.error_rate = 25.0
            self.queue_depth = 5000
    
    def apply_action(self, action_type: str, target: str) -> Tuple[bool, str]:
        """
        Apply an action to the system.
        Returns (success, message).
        """
        if action_type == "restart_service":
            return self._restart_service(target)
        elif action_type == "scale_service":
            return self._scale_service(target)
        elif action_type == "rollback_deployment":
            return self._rollback_deployment(target)
        elif action_type == "apply_patch":
            return self._apply_patch(target)
        elif action_type in ["inspect_logs", "check_metrics", "do_nothing"]:
            return True, f"Performed {action_type}"
        else:
            return False, "Unknown action"
    
    def _restart_service(self, target: str) -> Tuple[bool, str]:
        """Restart a service."""
        if target == "api":
            if self.root_cause == "api_out_of_memory":
                self.api_status = "healthy"
                self.api_cpu = 25.0
                self.api_memory = 40.0
                self.error_rate = 0.1
                self.incident_active = False
                return True, "API service restarted successfully"
            else:
                self.api_status = "healthy"
                self.api_cpu = 25.0
                return True, "API restarted but issue persists"
                
        elif target == "database":
            self.db_status = "healthy"
            self.db_cpu = 30.0
            self.db_connections = 20
            return True, "Database restarted"
            
        elif target == "cache":
            if self.root_cause == "cache_invalidation_storm":
                self.cache_status = "healthy"
                self.cache_hit_rate = 0.85
                self.cache_memory = 45.0
                # Partial resolution - still need to fix cascade
                return True, "Cache restarted"
            else:
                self.cache_status = "healthy"
                return True, "Cache restarted"
                
        elif target == "queue":
            self.queue_status = "healthy"
            self.queue_depth = 50
            return True, "Queue service restarted"
        
        return False, "Invalid target"
    
    def _scale_service(self, target: str) -> Tuple[bool, str]:
        """Scale a service (add capacity)."""
        if target == "api":
            self.api_cpu = max(10.0, self.api_cpu * 0.6)
            self.api_latency = max(50.0, self.api_latency * 0.7)
            return True, "API scaled up"
            
        elif target == "database":
            if self.root_cause == "cache_invalidation_storm" and self.cache_status == "healthy":
                # Scaling DB after cache fix helps
                self.db_cpu = 35.0
                self.db_connections = 25
                self.db_status = "healthy"
                return True, "Database scaled successfully"
            else:
                self.db_cpu = max(20.0, self.db_cpu * 0.8)
                return True, "Database scaled"
                
        return True, f"{target} scaled"
    
    def _rollback_deployment(self, target: str) -> Tuple[bool, str]:
        """Rollback to previous deployment."""
        if target == "api" and self.root_cause == "cache_invalidation_storm":
            # Rollback fixes bad deployment causing cache storm
            if self.cache_status == "healthy" and self.db_status == "healthy":
                self.api_status = "healthy"
                self.api_latency = 50.0
                self.error_rate = 0.1
                self.incident_active = False
                return True, "Rollback successful - incident resolved"
            else:
                return True, "Rollback completed but dependencies still failing"
        else:
            return True, f"Rolled back {target} (no effect on current incident)"
    
    def _apply_patch(self, target: str) -> Tuple[bool, str]:
        """Apply a configuration patch."""
        if target == "database" and self.root_cause == "database_connection_pool_exhausted":
            # Patch increases connection pool limit
            self.db_connections = 40
            self.db_cpu = 40.0
            self.db_status = "healthy"
            self.api_status = "healthy"
            self.api_latency = 80.0
            self.error_rate = 0.2
            self.incident_active = False
            return True, "Patch applied - connection pool increased"
        else:
            return True, f"Patch applied to {target} (no effect)"
    
    def get_metrics(self, add_noise: bool = True) -> Metrics:
        """Get current metrics with optional noise."""
        metrics = Metrics(
            api_cpu=self.api_cpu,
            api_latency=self.api_latency,
            api_memory=self.api_memory,
            db_cpu=self.db_cpu,
            db_connections=self.db_connections,
            db_query_time=self.db_query_time,
            cache_hit_rate=self.cache_hit_rate,
            cache_memory=self.cache_memory,
            queue_depth=self.queue_depth,
            error_rate=self.error_rate
        )
        
        if add_noise:
            # Add realistic measurement noise
            metrics.api_cpu = max(0, min(100, metrics.api_cpu + self.rng.gauss(0, 2)))
            metrics.api_latency = max(0, metrics.api_latency + self.rng.gauss(0, 10))
            metrics.db_cpu = max(0, min(100, metrics.db_cpu + self.rng.gauss(0, 3)))
            metrics.cache_hit_rate = max(0, min(1, metrics.cache_hit_rate + self.rng.gauss(0, 0.02)))
            metrics.error_rate = max(0, metrics.error_rate + self.rng.gauss(0, 0.5))
        
        return metrics
    
    def get_logs(self, action_type: str = None) -> str:
        """Generate realistic logs based on system state."""
        logs = []
        timestamp_base = "2026-03-30T14:23:"
        
        # Add noise logs (realistic production chatter)
        if self.rng.random() < 0.3:
            logs.append(f"{timestamp_base}10 [INFO] API: Health check passed")
        if self.rng.random() < 0.2:
            logs.append(f"{timestamp_base}11 [INFO] Queue: Processed 150 messages")
        
        # Incident-specific logs
        if self.api_status == "down":
            logs.append(f"{timestamp_base}15 [ERROR] API: Process terminated with exit code 137")
            logs.append(f"{timestamp_base}15 [ERROR] API: java.lang.OutOfMemoryError: Java heap space")
            logs.append(f"{timestamp_base}16 [CRITICAL] LoadBalancer: No healthy API instances")
            
        elif self.api_status == "degraded":
            if self.root_cause == "database_connection_pool_exhausted":
                logs.append(f"{timestamp_base}18 [ERROR] API: Connection timeout after 5000ms")
                logs.append(f"{timestamp_base}18 [WARN] API: Retrying database connection (attempt 3/3)")
                logs.append(f"{timestamp_base}19 [ERROR] DB: Connection pool exhausted (100/100 active)")
                logs.append(f"{timestamp_base}19 [WARN] DB: Waiting for available connection")
            elif self.root_cause == "cache_invalidation_storm":
                logs.append(f"{timestamp_base}20 [ERROR] Cache: Connection refused (ECONNREFUSED)")
                logs.append(f"{timestamp_base}20 [WARN] API: Cache miss - falling back to database")
                logs.append(f"{timestamp_base}21 [ERROR] DB: Query timeout - too many concurrent requests")
                logs.append(f"{timestamp_base}21 [CRITICAL] API: Circuit breaker opened for database")
        
        if self.db_status == "degraded":
            logs.append(f"{timestamp_base}22 [WARN] DB: High CPU usage detected")
            logs.append(f"{timestamp_base}22 [WARN] DB: Slow query detected (2.3s)")
        
        if self.cache_status == "down":
            logs.append(f"{timestamp_base}24 [ERROR] Cache: Redis connection lost")
            logs.append(f"{timestamp_base}24 [ERROR] Cache: MAXMEMORY limit exceeded")
        
        # Action-specific logs
        if action_type == "inspect_logs":
            logs.append(f"{timestamp_base}30 [INFO] System: Deep log analysis initiated")
            if self.root_cause == "database_connection_pool_exhausted":
                logs.append(f"{timestamp_base}31 [DEBUG] DB: pool.maxConnections=100, pool.activeConnections=98")
            elif self.root_cause == "cache_invalidation_storm":
                logs.append(f"{timestamp_base}31 [DEBUG] API: Deployment v2.3.1 rolled out 10 minutes ago")
                logs.append(f"{timestamp_base}31 [DEBUG] Cache: Eviction rate: 1000 keys/sec")
        
        if not logs:
            logs.append(f"{timestamp_base}35 [INFO] System: No critical errors in recent logs")
        
        return "\n".join(logs)
    
    def get_alerts(self) -> List[str]:
        """Generate active alerts based on system state."""
        alerts = []
        
        if self.api_status == "down":
            alerts.append("CRITICAL: API_SERVICE_DOWN")
        elif self.api_status == "degraded":
            alerts.append("WARNING: API_DEGRADED_PERFORMANCE")
        
        if self.api_latency > 1000:
            alerts.append("WARNING: HIGH_API_LATENCY")
        
        if self.db_cpu > 80:
            alerts.append("WARNING: HIGH_DB_CPU")
        
        if self.db_connections > 90:
            alerts.append("CRITICAL: DB_CONNECTION_POOL_NEAR_LIMIT")
        
        if self.cache_status == "down":
            alerts.append("CRITICAL: CACHE_SERVICE_DOWN")
        
        if self.cache_hit_rate < 0.5:
            alerts.append("WARNING: LOW_CACHE_HIT_RATE")
        
        if self.error_rate > 10:
            alerts.append("CRITICAL: HIGH_ERROR_RATE")
        
        if self.queue_depth > 1000:
            alerts.append("WARNING: MESSAGE_QUEUE_BACKLOG")
        
        return alerts
    
    def is_system_healthy(self) -> bool:
        """Check if system is fully recovered."""
        return (
            self.api_status == "healthy" and
            self.db_status == "healthy" and
            self.cache_status == "healthy" and
            self.queue_status == "healthy" and
            self.error_rate < 1.0 and
            self.api_latency < 200
        )
    
    def simulate_time_step(self):
        """Simulate natural system evolution over one time step."""
        # Gradual recovery for transient issues
        if self.api_status == "degraded" and self.rng.random() < 0.1:
            self.api_latency = max(50, self.api_latency * 0.9)
        
        # Degradation if incident not resolved
        if self.incident_active:
            if self.db_status == "degraded":
                self.db_cpu = min(100, self.db_cpu + self.rng.uniform(0, 2))
            if self.cache_status == "down":
                # Cache down increases DB load
                self.db_cpu = min(100, self.db_cpu + self.rng.uniform(1, 3))
                self.db_connections = min(100, self.db_connections + self.rng.randint(0, 2))


class IncidentGenerator:
    """Generates randomized incidents with configurable difficulty."""
    
    INCIDENT_TYPES = [
        "api_crash",
        "db_connection_exhaustion", 
        "cache_failure_cascade",
        "memory_leak",
        "db_deadlock",
        "network_latency_spike",
        "disk_space_exhaustion",
        "deployment_bug"
    ]
    
    @staticmethod
    def generate_random_incident(difficulty: str = "medium", seed: Optional[int] = None) -> Dict:
        """Generate a random incident configuration."""
        rng = random.Random(seed)
        
        if difficulty == "easy":
            incident_types = ["api_crash", "memory_leak"]
        elif difficulty == "medium":
            incident_types = ["db_connection_exhaustion", "network_latency_spike", "deployment_bug"]
        else:  # hard
            incident_types = ["cache_failure_cascade", "db_deadlock", "disk_space_exhaustion"]
        
        incident_type = rng.choice(incident_types)
        
        return {
            "type": incident_type,
            "severity": rng.choice(["high", "critical"]),
            "cascading": difficulty == "hard",
            "noise_level": 0.1 if difficulty == "easy" else 0.3 if difficulty == "medium" else 0.5
        }
