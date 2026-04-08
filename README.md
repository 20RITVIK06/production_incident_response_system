# Production Incident Response Simulator

A realistic OpenEnv-compatible reinforcement learning environment simulating production incident debugging and resolution in a distributed microservices system.

## Problem Motivation

Modern production systems fail in complex ways. When incidents occur, DevOps engineers must:
- Parse noisy logs and metrics
- Diagnose root causes under pressure
- Choose optimal remediation actions
- Balance speed vs. risk

This environment trains AI agents to handle real-world incident response scenarios with partial observability, misleading signals, and cascading failures.

## System Architecture

Simulates a microservices stack:
- **API Service**: Frontend-facing REST API
- **Database**: PostgreSQL backend
- **Cache**: Redis layer
- **Queue**: Message broker (RabbitMQ)

Each component has:
- Health status
- Performance metrics (CPU, memory, latency)
- Error rates
- Logs with realistic noise

## Action Space

7 discrete actions representing DevOps interventions:

| Action | Description | Use Case |
|--------|-------------|----------|
| `restart_service` | Restart a failing service | Service crashes, memory leaks |
| `scale_service` | Add capacity | High load, performance degradation |
| `rollback_deployment` | Revert to previous version | Bad deployment, new bugs |
| `inspect_logs` | Deep dive into logs | Diagnosis, root cause analysis |
| `check_metrics` | Query detailed metrics | Performance investigation |
| `apply_patch` | Hot-fix without restart | Config errors, minor bugs |
| `do_nothing` | Wait and observe | Transient issues, gathering info |

## Observation Space

Partial observability with realistic noise:

```python
{
    "logs": str,           # Recent log entries (errors, warnings, info)
    "metrics": {
        "api_cpu": float,      # 0-100%
        "api_latency": float,  # milliseconds
        "db_cpu": float,
        "db_connections": int,
        "cache_hit_rate": float,
        "queue_depth": int,
        "error_rate": float    # errors/sec
    },
    "alerts": [str],       # Active alerts
    "time_elapsed": int    # Steps taken
}
```

## Tasks

### EASY: Service Crash
- **Scenario**: API service crashed due to OOM
- **Clear Signal**: Obvious error in logs
- **Solution**: Restart service
- **Steps**: 1-2 actions

### MEDIUM: Database Connection Pool Exhaustion
- **Scenario**: Connection leak causing cascading failures
- **Misleading**: API shows errors, but root cause is DB config
- **Solution**: Apply patch to increase pool size + restart
- **Steps**: 3-4 actions with diagnosis

### HARD: Cascading Failure from Cache Invalidation Storm
- **Scenario**: Cache failure → DB overload → API degradation
- **Complex**: Multiple components failing, conflicting signals
- **Solution**: Restart cache, scale DB, then rollback bad deployment
- **Steps**: 5+ actions requiring strategic planning

## Reward Function

Designed to encourage efficient, correct incident resolution:

**Positive Rewards:**
- `+1.0`: Incident fully resolved
- `+0.2`: Correct diagnosis step
- `+0.1`: Helpful action

**Penalties:**
- `-0.1`: Useless action
- `-0.3`: Wrong fix attempt
- `-0.5`: System degradation caused
- `-0.05`: Per time step (efficiency pressure)

**Terminal Rewards:**
- Success: Base reward + time bonus
- Failure: Accumulated penalties

## Grader System

Each task includes a deterministic grader evaluating:
1. **Correctness** (60%): Did agent resolve the incident?
2. **Efficiency** (30%): Steps taken vs. optimal path
3. **Safety** (10%): Avoided harmful actions

Score normalized to [0.0, 1.0] for reproducibility.

## Installation

```bash
# Clone repository
git clone <repo-url>
cd production-incident-simulator

# Install dependencies
pip install -r requirements.txt

# Validate environment
python -m openenv.validate openenv.yaml
```

## Usage

### Basic Usage

```python
from env import ProductionIncidentEnv

env = ProductionIncidentEnv(task="easy")
obs = env.reset()

done = False
while not done:
    action = agent.select_action(obs)
    obs, reward, done, info = env.step(action)
    
print(f"Score: {info['score']}")
```

### Run Baseline Agent

```bash
# Set OpenAI API key
export OPENAI_API_KEY=your_key_here

# Run baseline on all tasks
python inference.py

# Run specific task
python inference.py --task medium
```

### Docker Deployment

```bash
# Build image
docker build -t incident-simulator .

# Run container
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY incident-simulator
```

## Baseline Results

GPT-4 baseline performance:

| Task | Score | Steps | Success Rate |
|------|-------|-------|--------------|
| Easy | 0.85 | 2.3 | 95% |
| Medium | 0.62 | 4.7 | 70% |
| Hard | 0.41 | 8.2 | 35% |

## Advanced Features

### Randomized Incidents

```python
env = ProductionIncidentEnv(task="random", difficulty="hard")
```

Generates random failures:
- Memory leaks
- Database deadlocks
- Network latency spikes
- Cache stampedes
- Deployment bugs

### Configurable Difficulty

```python
env = ProductionIncidentEnv(
    task="medium",
    noise_level=0.3,      # Log/metric noise
    max_steps=15,         # Time pressure
    cascading_prob=0.4    # Failure propagation
)
```

## Project Structure

```
.
├── env.py                 # Main environment implementation
├── models.py              # Pydantic models (Observation, Action, Reward)
├── tasks.py               # Task definitions and graders
├── system_simulator.py    # Microservices system simulation
├── inference.py           # Baseline agent
├── openenv.yaml           # OpenEnv metadata
├── requirements.txt       # Dependencies
├── Dockerfile            # Container definition
├── README.md             # This file
└── tests/
    └── test_env.py       # Validation tests
```

## Development

```bash
# Run tests
pytest tests/

# Validate OpenEnv compliance
python -m openenv.validate openenv.yaml

# Type checking
mypy env.py models.py
```

## Citation

If you use this environment in research:

```bibtex
@software{production_incident_simulator,
  title={Production Incident Response Simulator},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/incident-simulator}
}
```

## License

MIT License - See LICENSE file for details
