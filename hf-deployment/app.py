"""
Hugging Face Spaces Gradio interface.
Interactive demo of the incident response simulator.
"""

try:
    import gradio as gr
except ImportError:
    print("Gradio not installed. Install with: pip install gradio")
    exit(1)

from env import ProductionIncidentEnv
from models import Action
import json


class InteractiveDemo:
    """Interactive demo wrapper for Gradio."""
    
    def __init__(self):
        self.env = None
        self.current_obs = None
        self.episode_history = []
    
    def start_episode(self, task: str, seed: int):
        """Start a new episode."""
        self.env = ProductionIncidentEnv(task=task, seed=seed)
        self.current_obs = self.env.reset()
        self.episode_history = []
        
        return self._format_observation(), "Episode started! Choose your first action.", ""
    
    def take_action(self, action_type: str, target: str):
        """Take an action in the environment."""
        if self.env is None:
            return "Please start an episode first!", "", ""
        
        try:
            action = Action(
                action_type=action_type,
                target=target if target != "none" else None
            )
            
            obs, reward, done, info = self.env.step(action)
            self.current_obs = obs
            
            # Record history
            self.episode_history.append({
                "step": obs.time_elapsed,
                "action": f"{action_type}:{target}",
                "reward": reward.total,
                "done": done
            })
            
            # Format response
            obs_text = self._format_observation()
            
            status = f"Reward: {reward.total:+.2f} | {info.get('message', '')}"
            
            if done:
                episode_info = info.get("episode", {})
                status += f"\n\nEPISODE COMPLETE!\n"
                status += f"Success: {episode_info.get('success', False)}\n"
                status += f"Score: {episode_info.get('score', 0.0):.3f}\n"
                status += f"Steps: {episode_info.get('steps_taken', 0)}\n"
                status += f"Root Cause: {episode_info.get('root_cause', 'unknown')}"
            
            history_text = self._format_history()
            
            return obs_text, status, history_text
        
        except Exception as e:
            return str(e), "Error occurred", ""
    
    def _format_observation(self):
        """Format observation for display."""
        if self.current_obs is None:
            return "No observation available"
        
        obs = self.current_obs
        
        text = f"""### Logs
```
{obs.logs}
```

### Metrics
- **API**: CPU={obs.metrics.api_cpu:.1f}%, Latency={obs.metrics.api_latency:.0f}ms, Memory={obs.metrics.api_memory:.1f}%
- **Database**: CPU={obs.metrics.db_cpu:.1f}%, Connections={obs.metrics.db_connections}, QueryTime={obs.metrics.db_query_time:.0f}ms
- **Cache**: HitRate={obs.metrics.cache_hit_rate:.2f}, Memory={obs.metrics.cache_memory:.1f}%
- **Queue**: Depth={obs.metrics.queue_depth}
- **Error Rate**: {obs.metrics.error_rate:.1f}/sec

### Active Alerts
{chr(10).join('- ' + alert for alert in obs.alerts) if obs.alerts else 'No active alerts'}

**Time Elapsed**: {obs.time_elapsed} steps
"""
        return text
    
    def _format_history(self):
        """Format episode history."""
        if not self.episode_history:
            return "No actions taken yet"
        
        history = "### Action History\n\n"
        for entry in self.episode_history:
            history += f"Step {entry['step']}: {entry['action']} → Reward: {entry['reward']:+.2f}\n"
        
        return history


# Create demo instance
demo = InteractiveDemo()


# Build Gradio interface
with gr.Blocks(title="Production Incident Response Simulator") as app:
    gr.Markdown("""
    # 🚨 Production Incident Response Simulator
    
    Train AI agents to handle production incidents in a realistic microservices environment.
    
    **How to use:**
    1. Select a task difficulty and start an episode
    2. Read the logs, metrics, and alerts
    3. Choose actions to diagnose and resolve the incident
    4. Try to resolve it in as few steps as possible!
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Episode Configuration")
            task_dropdown = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="easy",
                label="Task Difficulty"
            )
            seed_input = gr.Number(value=42, label="Random Seed", precision=0)
            start_btn = gr.Button("Start Episode", variant="primary")
            
            gr.Markdown("### Take Action")
            action_dropdown = gr.Dropdown(
                choices=[
                    "restart_service",
                    "scale_service",
                    "rollback_deployment",
                    "inspect_logs",
                    "check_metrics",
                    "apply_patch",
                    "do_nothing"
                ],
                value="inspect_logs",
                label="Action Type"
            )
            target_dropdown = gr.Dropdown(
                choices=["api", "database", "cache", "queue", "none"],
                value="none",
                label="Target Service"
            )
            action_btn = gr.Button("Execute Action", variant="secondary")
        
        with gr.Column(scale=2):
            gr.Markdown("### Current Observation")
            observation_display = gr.Markdown("Start an episode to see observations")
            
            gr.Markdown("### Status")
            status_display = gr.Textbox(label="", lines=3, interactive=False)
    
    with gr.Row():
        history_display = gr.Markdown("### Episode History\nNo actions taken yet")
    
    # Event handlers
    start_btn.click(
        fn=demo.start_episode,
        inputs=[task_dropdown, seed_input],
        outputs=[observation_display, status_display, history_display]
    )
    
    action_btn.click(
        fn=demo.take_action,
        inputs=[action_dropdown, target_dropdown],
        outputs=[observation_display, status_display, history_display]
    )
    
    gr.Markdown("""
    ---
    ### About the Environment
    
    This OpenEnv-compatible environment simulates realistic production incidents:
    - **Easy**: Simple service crashes with clear signals
    - **Medium**: Resource exhaustion requiring diagnosis
    - **Hard**: Cascading failures with conflicting signals
    
    **Action Space**: 7 DevOps interventions (restart, scale, rollback, inspect, check, patch, wait)
    
    **Reward Function**: Balances correctness, efficiency, and safety
    
    [GitHub Repository](https://github.com/yourusername/incident-simulator) | [Documentation](README.md)
    """)


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
