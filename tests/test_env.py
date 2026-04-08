"""
Test suite for Production Incident Response Simulator.
Validates OpenEnv compliance and environment behavior.
"""

import pytest
from env import ProductionIncidentEnv
from models import Action, Observation, Reward, SystemState
from tasks import TASKS


class TestEnvironmentBasics:
    """Test basic environment functionality."""
    
    def test_environment_initialization(self):
        """Test environment can be initialized."""
        env = ProductionIncidentEnv(task="easy")
        assert env is not None
        assert env.task_name == "easy"
    
    def test_reset(self):
        """Test environment reset."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        obs = env.reset()
        
        assert isinstance(obs, Observation)
        assert obs.time_elapsed == 0
        assert obs.logs is not None
        assert obs.metrics is not None
        assert isinstance(obs.alerts, list)
    
    def test_step(self):
        """Test environment step."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        action = Action(action_type="inspect_logs")
        obs, reward, done, info = env.step(action)
        
        assert isinstance(obs, Observation)
        assert isinstance(reward, Reward)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
    
    def test_state(self):
        """Test state() returns full system state."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        state = env.state()
        assert isinstance(state, SystemState)
        assert state.root_cause is not None
        assert state.incident_type is not None


class TestTasks:
    """Test all task scenarios."""
    
    def test_easy_task(self):
        """Test easy task can be completed."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        # Optimal solution: inspect logs, restart API
        action1 = Action(action_type="inspect_logs")
        obs, reward, done, info = env.step(action1)
        assert not done
        
        action2 = Action(action_type="restart_service", target="api")
        obs, reward, done, info = env.step(action2)
        
        # Should resolve incident
        assert info.get("system_healthy", False) or done
    
    def test_medium_task(self):
        """Test medium task initialization."""
        env = ProductionIncidentEnv(task="medium", seed=42)
        obs = env.reset()
        
        assert env._current_task.name == "medium"
        assert "database" in env._state.root_cause.lower() or "connection" in env._state.root_cause.lower()
    
    def test_hard_task(self):
        """Test hard task initialization."""
        env = ProductionIncidentEnv(task="hard", seed=42)
        obs = env.reset()
        
        assert env._current_task.name == "hard"
        assert "cache" in env._state.root_cause.lower()


class TestActions:
    """Test all action types."""
    
    @pytest.fixture
    def env(self):
        """Create environment for testing."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        return env
    
    def test_restart_service(self, env):
        """Test restart_service action."""
        action = Action(action_type="restart_service", target="api")
        obs, reward, done, info = env.step(action)
        assert "restart" in info["message"].lower()
    
    def test_scale_service(self, env):
        """Test scale_service action."""
        action = Action(action_type="scale_service", target="database")
        obs, reward, done, info = env.step(action)
        assert "scale" in info["message"].lower()
    
    def test_rollback_deployment(self, env):
        """Test rollback_deployment action."""
        action = Action(action_type="rollback_deployment", target="api")
        obs, reward, done, info = env.step(action)
        assert "rolled back" in info["message"].lower() or "rollback" in info["message"].lower()
    
    def test_inspect_logs(self, env):
        """Test inspect_logs action."""
        action = Action(action_type="inspect_logs")
        obs, reward, done, info = env.step(action)
        assert obs.logs is not None
    
    def test_check_metrics(self, env):
        """Test check_metrics action."""
        action = Action(action_type="check_metrics")
        obs, reward, done, info = env.step(action)
        assert obs.metrics is not None
    
    def test_apply_patch(self, env):
        """Test apply_patch action."""
        action = Action(action_type="apply_patch", target="database")
        obs, reward, done, info = env.step(action)
        assert "patch" in info["message"].lower()
    
    def test_do_nothing(self, env):
        """Test do_nothing action."""
        action = Action(action_type="do_nothing")
        obs, reward, done, info = env.step(action)
        assert not done or env._state.steps_taken >= env.max_steps


class TestRewards:
    """Test reward function."""
    
    def test_reward_structure(self):
        """Test reward has correct structure."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        action = Action(action_type="inspect_logs")
        obs, reward, done, info = env.step(action)
        
        assert hasattr(reward, "total")
        assert hasattr(reward, "correctness")
        assert hasattr(reward, "efficiency")
        assert hasattr(reward, "safety")
        assert hasattr(reward, "progress")
    
    def test_time_penalty(self):
        """Test time penalty is applied."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        action = Action(action_type="do_nothing")
        obs, reward, done, info = env.step(action)
        
        # Should have negative efficiency component
        assert reward.efficiency < 0


class TestTermination:
    """Test episode termination conditions."""
    
    def test_max_steps_termination(self):
        """Test episode terminates after max steps."""
        env = ProductionIncidentEnv(task="easy", max_steps=5, seed=42)
        env.reset()
        
        done = False
        steps = 0
        while not done and steps < 10:
            action = Action(action_type="do_nothing")
            obs, reward, done, info = env.step(action)
            steps += 1
        
        assert done
        assert steps <= 5
    
    def test_success_termination(self):
        """Test episode terminates on success."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        # Solve the incident
        action1 = Action(action_type="inspect_logs")
        env.step(action1)
        
        action2 = Action(action_type="restart_service", target="api")
        obs, reward, done, info = env.step(action2)
        
        # Should eventually terminate
        if not done:
            # May need one more step for system to stabilize
            action3 = Action(action_type="check_metrics")
            obs, reward, done, info = env.step(action3)


class TestObservability:
    """Test partial observability and noise."""
    
    def test_observation_has_noise(self):
        """Test observations include noise."""
        env1 = ProductionIncidentEnv(task="easy", seed=42, noise_level=0.0)
        obs1 = env1.reset()
        
        env2 = ProductionIncidentEnv(task="easy", seed=43, noise_level=0.5)
        obs2 = env2.reset()
        
        # Different seeds should produce different observations
        # (though same task, so root cause is same)
        assert obs1.metrics.api_cpu != obs2.metrics.api_cpu or \
               obs1.metrics.db_cpu != obs2.metrics.db_cpu
    
    def test_hidden_state(self):
        """Test root cause is hidden from observation."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        obs = env.reset()
        
        # Observation should not directly reveal root cause
        assert not hasattr(obs, "root_cause")
        
        # But state() should reveal it
        state = env.state()
        assert state.root_cause is not None


class TestDeterminism:
    """Test environment determinism with seeds."""
    
    def test_same_seed_same_behavior(self):
        """Test same seed produces same behavior."""
        env1 = ProductionIncidentEnv(task="easy", seed=42)
        obs1 = env1.reset()
        
        env2 = ProductionIncidentEnv(task="easy", seed=42)
        obs2 = env2.reset()
        
        # Same seed should produce identical initial observations
        assert obs1.metrics.api_cpu == obs2.metrics.api_cpu
        assert obs1.metrics.db_cpu == obs2.metrics.db_cpu
        assert obs1.alerts == obs2.alerts


class TestGrading:
    """Test grading system."""
    
    def test_grading_on_success(self):
        """Test grading produces score on episode end."""
        env = ProductionIncidentEnv(task="easy", seed=42)
        env.reset()
        
        # Complete episode
        done = False
        while not done:
            action = Action(action_type="restart_service", target="api")
            obs, reward, done, info = env.step(action)
            
            if env._state.steps_taken >= env.max_steps:
                break
        
        if done and "episode" in info:
            episode_info = info["episode"]
            assert "score" in episode_info
            assert 0.0 <= episode_info["score"] <= 1.0
            assert "success" in episode_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
