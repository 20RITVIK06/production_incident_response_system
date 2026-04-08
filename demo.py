"""
Comprehensive demo showcasing all environment features.
Run this to see the simulator in action.
"""

from env import ProductionIncidentEnv
from models import Action
from advanced_incidents import ConfigurableIncidentEnv, generate_random_incident_config
import time


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_observation(obs):
    """Print formatted observation."""
    print("📊 OBSERVATION:")
    print(f"\n📝 Logs:\n{obs.logs}\n")
    print(f"📈 Key Metrics:")
    print(f"  • API: {obs.metrics.api_cpu:.1f}% CPU, {obs.metrics.api_latency:.0f}ms latency")
    print(f"  • DB: {obs.metrics.db_cpu:.1f}% CPU, {obs.metrics.db_connections} connections")
    print(f"  • Cache: {obs.metrics.cache_hit_rate:.1%} hit rate")
    print(f"  • Errors: {obs.metrics.error_rate:.1f}/sec")
    print(f"\n🚨 Alerts: {', '.join(obs.alerts) if obs.alerts else 'None'}")
    print(f"⏱️  Time: {obs.time_elapsed} steps\n")


def demo_easy_task():
    """Demo 1: Easy task walkthrough."""
    print_header("DEMO 1: Easy Task - API Service Crash")
    
    env = ProductionIncidentEnv(task="easy", seed=42)
    obs = env.reset()
    
    print("🎯 Scenario: API service crashed due to out-of-memory error")
    print("🎯 Goal: Diagnose and restart the service\n")
    
    print_observation(obs)
    
    # Step 1: Inspect logs
    print("🤖 Agent Action: inspect_logs")
    action = Action(action_type="inspect_logs")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f} (correctness: {reward.correctness:+.2f})")
    print(f"💬 Result: {info['message']}\n")
    
    # Step 2: Restart API
    print("🤖 Agent Action: restart_service -> api")
    action = Action(action_type="restart_service", target="api")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f} (correctness: {reward.correctness:+.2f})")
    print(f"💬 Result: {info['message']}")
    
    if done:
        print(f"\n✅ INCIDENT RESOLVED!")
        print(f"📊 Final Score: {info['score']:.3f}")
        print(f"⏱️  Steps Taken: {info['episode']['steps_taken']} (optimal: {info['episode']['optimal_steps']})")


def demo_medium_task():
    """Demo 2: Medium task walkthrough."""
    print_header("DEMO 2: Medium Task - Database Connection Pool Exhaustion")
    
    env = ProductionIncidentEnv(task="medium", seed=42)
    obs = env.reset()
    
    print("🎯 Scenario: Database connection pool exhausted")
    print("🎯 Goal: Diagnose root cause and apply fix\n")
    
    print_observation(obs)
    
    # Step 1: Inspect logs
    print("🤖 Agent Action: inspect_logs")
    action = Action(action_type="inspect_logs")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f}")
    print(f"💬 Analysis: Logs show 'Connection pool exhausted (100/100 active)'\n")
    
    # Step 2: Apply patch
    print("🤖 Agent Action: apply_patch -> database")
    action = Action(action_type="apply_patch", target="database")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f}")
    print(f"💬 Result: {info['message']}")
    
    if done:
        print(f"\n✅ INCIDENT RESOLVED!")
        print(f"📊 Final Score: {info['score']:.3f}")


def demo_hard_task():
    """Demo 3: Hard task walkthrough."""
    print_header("DEMO 3: Hard Task - Cascading Cache Failure")
    
    env = ProductionIncidentEnv(task="hard", seed=42)
    obs = env.reset()
    
    print("🎯 Scenario: Cache failure causing DB overload and API degradation")
    print("🎯 Goal: Multi-step resolution of cascading failure\n")
    
    print_observation(obs)
    
    steps = [
        ("inspect_logs", None, "Diagnose the issue"),
        ("restart_service", "cache", "Fix cache service"),
        ("scale_service", "database", "Handle DB overload"),
        ("rollback_deployment", "api", "Rollback bad deployment")
    ]
    
    for action_type, target, description in steps:
        print(f"🤖 Agent Action: {action_type}" + (f" -> {target}" if target else ""))
        print(f"   Reasoning: {description}")
        
        action = Action(action_type=action_type, target=target)
        obs, reward, done, info = env.step(action)
        
        print(f"💰 Reward: {reward.total:+.2f}")
        print(f"💬 Result: {info['message']}\n")
        
        if done:
            break
    
    if done:
        print(f"✅ INCIDENT RESOLVED!")
        print(f"📊 Final Score: {info['score']:.3f}")
        print(f"⏱️  Steps: {info['episode']['steps_taken']} (optimal: {info['episode']['optimal_steps']})")


def demo_wrong_actions():
    """Demo 4: Show penalty for wrong actions."""
    print_header("DEMO 4: Learning from Mistakes")
    
    env = ProductionIncidentEnv(task="easy", seed=42)
    obs = env.reset()
    
    print("🎯 Demonstrating penalties for incorrect actions\n")
    
    # Wrong action: Scale when should restart
    print("🤖 Agent Action: scale_service -> api (WRONG)")
    action = Action(action_type="scale_service", target="api")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f} (correctness: {reward.correctness:+.2f})")
    print(f"💬 Result: Scaling doesn't fix a crashed service\n")
    
    # Harmful action: Restart healthy service
    print("🤖 Agent Action: restart_service -> database (HARMFUL)")
    action = Action(action_type="restart_service", target="database")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f} (safety: {reward.safety:+.2f})")
    print(f"💬 Result: Restarting healthy services causes unnecessary downtime\n")
    
    # Correct action
    print("🤖 Agent Action: restart_service -> api (CORRECT)")
    action = Action(action_type="restart_service", target="api")
    obs, reward, done, info = env.step(action)
    print(f"💰 Reward: {reward.total:+.2f} (correctness: {reward.correctness:+.2f})")
    print(f"💬 Result: {info['message']}\n")
    
    if done:
        print(f"📊 Final Score: {info['score']:.3f}")
        print(f"⚠️  Harmful Actions: {info['episode']['harmful_actions']}")


def demo_random_incidents():
    """Demo 5: Random incident generation."""
    print_header("DEMO 5: Random Incident Generation")
    
    print("Generating 3 random incidents:\n")
    
    for i in range(3):
        config = generate_random_incident_config(
            difficulty=["easy", "medium", "hard"][i],
            seed=i
        )
        print(f"Incident {i+1} ({config['difficulty'].upper()}):")
        print(f"  Type: {config['incident_type']}")
        print(f"  Max Steps: {config['max_steps']}")
        print(f"  Noise Level: {config['noise_level']}")
        print(f"  Cascading: {config['cascading_failures']}\n")


def demo_state_inspection():
    """Demo 6: Internal state inspection."""
    print_header("DEMO 6: State Inspection (Debugging)")
    
    env = ProductionIncidentEnv(task="hard", seed=42)
    obs = env.reset()
    
    print("🔍 Comparing Observable vs. Hidden Information:\n")
    
    state = env.state()
    
    print("👁️  OBSERVABLE (what agent sees):")
    print(f"  • Alerts: {obs.alerts[:2]}...")
    print(f"  • API Latency: {obs.metrics.api_latency:.0f}ms")
    print(f"  • DB CPU: {obs.metrics.db_cpu:.1f}%")
    print(f"  • Error Rate: {obs.metrics.error_rate:.1f}/sec\n")
    
    print("🔒 HIDDEN (ground truth):")
    print(f"  • Root Cause: {state.root_cause}")
    print(f"  • Incident Type: {state.incident_type}")
    print(f"  • API Status: {state.api_status}")
    print(f"  • DB Status: {state.db_status}")
    print(f"  • Cache Status: {state.cache_status}\n")
    
    print("💡 Agent must infer root cause from observable signals!")


def demo_all():
    """Run all demos."""
    print("\n" + "🚨"*35)
    print("  PRODUCTION INCIDENT RESPONSE SIMULATOR - COMPLETE DEMO")
    print("🚨"*35)
    
    demos = [
        demo_easy_task,
        demo_medium_task,
        demo_hard_task,
        demo_wrong_actions,
        demo_random_incidents,
        demo_state_inspection
    ]
    
    for demo_func in demos:
        demo_func()
        time.sleep(1)  # Pause between demos
    
    print_header("DEMO COMPLETE")
    print("✅ All features demonstrated successfully!")
    print("\nNext steps:")
    print("  • Run baseline: python inference.py")
    print("  • Run tests: pytest tests/ -v")
    print("  • Try Gradio: python app.py")
    print("  • Read docs: README.md\n")


if __name__ == "__main__":
    demo_all()
