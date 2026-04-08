"""
OpenEnv API server for hackathon submission.
Provides REST endpoints for environment interaction.
"""
from flask import Flask, request, jsonify
from env import ProductionIncidentEnv
from models import Action
import os

app = Flask(__name__)

# Global environment instance
env_instance = None
current_task = "easy"

@app.route('/reset', methods=['POST'])
def reset():
    """Reset environment endpoint."""
    global env_instance, current_task
    
    try:
        # Get task from request if provided
        data = request.get_json(force=True, silent=True) or {}
        task = data.get('task', current_task)
        seed = data.get('seed', 42)
        
        # Create new environment
        env_instance = ProductionIncidentEnv(task=task, seed=seed)
        obs = env_instance.reset()
        
        return jsonify({
            'observation': obs.model_dump(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/step', methods=['POST'])
def step():
    """Step environment endpoint."""
    global env_instance
    
    if env_instance is None:
        return jsonify({
            'error': 'Environment not initialized. Call /reset first.',
            'status': 'error'
        }), 400
    
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'status': 'error'
            }), 400
            
        action = Action(**data)
        
        obs, reward, done, info = env_instance.step(action)
        
        return jsonify({
            'observation': obs.model_dump(),
            'reward': reward.model_dump(),
            'done': done,
            'info': info,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/state', methods=['GET'])
def state():
    """Get current state endpoint."""
    global env_instance
    
    if env_instance is None:
        return jsonify({
            'error': 'Environment not initialized. Call /reset first.',
            'status': 'error'
        }), 400
    
    try:
        current_state = env_instance.state()
        return jsonify({
            'state': current_state.model_dump(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        'name': 'Production Incident Response Simulator',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'POST /reset': 'Reset environment (body: {task, seed})',
            'POST /step': 'Take action (body: {action_type, target})',
            'GET /state': 'Get current state',
            'GET /health': 'Health check'
        },
        'tasks': ['easy', 'medium', 'hard'],
        'actions': ['restart_service', 'scale_service', 'rollback_deployment', 
                   'inspect_logs', 'check_metrics', 'apply_patch', 'do_nothing']
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'environment': 'production-incident-response-simulator'
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)
