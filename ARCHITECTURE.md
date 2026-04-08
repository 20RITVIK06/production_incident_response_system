# Architecture Documentation

## System Design

### Overview

The Production Incident Response Simulator is built with modularity and realism in mind. It simulates a production microservices environment where incidents occur and must be resolved through strategic actions.

### Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ProductionIncidentEnv                  │
│                  (OpenEnv Interface)                     │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   reset()  │  │    step()    │  │    state()     │  │
│  └────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
           │                    │                  │
           ▼                    ▼                  ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│ MicroserviceSystem│  │   Task Manager   │  │ Reward Engine│
│                  │  │                  │  │              │
│ - API Service    │  │ - Easy Task      │  │ - Correctness│
│ - Database       │  │ - Medium Task    │  │ - Efficiency │
│ - Cache          │  │ - Hard Task      │  │ - Safety     │
│ - Queue          │  │ - Grading Logic  │  │ - Progress   │
└──────────────────┘  └──────────────────┘  └──────────────┘
```

### Data Flow

1. **Initialization**: Environment loads task definition and initializes system simulator
2. **Reset**: System injected with incident, initial observation generated
3. **Step Loop**:
   - Agent receives observation (logs, metrics, alerts)
   - Agent selects action
   - System simulator applies action
   - Reward calculated based on action correctness
   - New observation generated
   - Termination checked
4. **Grading**: Episode scored on correctness, efficiency, safety

### Key Design Decisions

#### Partial Observability

Agents don't see:
- Root cause directly
- Internal service state
- Future consequences of actions

Agents only see:
- Logs (with noise)
- Metrics (with measurement error)
- Alerts (derived from metrics)

This mirrors real production debugging where engineers must infer root causes.

#### Realistic Noise

- **Metric Noise**: Gaussian noise on measurements (±2-3%)
- **Log Noise**: Irrelevant log entries mixed in (30% probability)
- **Misleading Signals**: Symptoms vs. root causes (e.g., API errors from DB issues)

#### Cascading Failures

Hard tasks include cascading failures:
- Cache failure → DB overload → API degradation
- Requires multi-step resolution
- Order matters (fix cache before scaling DB)

#### Reward Shaping

Reward function encourages:
- **Diagnosis first**: +0.2 for correct diagnostic actions
- **Targeted fixes**: +0.1 for helpful actions
- **Efficiency**: -0.05 per step (time pressure)
- **Safety**: -0.3 for harmful actions

Terminal rewards:
- **Success**: +1.0 base + time bonus
- **Failure**: Accumulated penalties only

### Extensibility

#### Adding New Incidents

1. Add incident type to `AdvancedIncidentSimulator.inject_incident()`
2. Define system state changes
3. Add corresponding logs in `get_logs()`
4. Create task definition in `tasks.py`

#### Adding New Actions

1. Add action to `ACTION_SPACE` in `env.py`
2. Implement handler in `MicroserviceSystem.apply_action()`
3. Update reward logic in `_is_correct_action()`
4. Update documentation

#### Custom Metrics

Add new metrics to `Metrics` model in `models.py`:
```python
class Metrics(BaseModel):
    # Existing metrics...
    custom_metric: float = Field(description="Your metric")
```

Then update `MicroserviceSystem.get_metrics()` to populate it.

## Performance Considerations

- **Episode Runtime**: ~0.1-0.5 seconds per step
- **Memory Usage**: <50MB per environment instance
- **Determinism**: Fully deterministic with seed
- **Parallelization**: Multiple environments can run in parallel

## Testing Strategy

- **Unit Tests**: Individual components (system simulator, reward function)
- **Integration Tests**: Full episode runs
- **Determinism Tests**: Seed reproducibility
- **Validation Tests**: OpenEnv spec compliance

## Deployment

### Local Development
```bash
pip install -r requirements.txt
python example_usage.py
```

### Docker
```bash
docker build -t incident-simulator .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY incident-simulator
```

### Hugging Face Spaces
- Upload repository to HF Space
- Set `OPENAI_API_KEY` in Space secrets
- App runs automatically via `app.py`

## Future Enhancements

1. **Multi-agent scenarios**: Multiple agents collaborating
2. **Real telemetry data**: Train on actual production logs
3. **Cost modeling**: Include infrastructure cost in rewards
4. **Human-in-the-loop**: Allow human override/guidance
5. **Visualization**: Real-time system state visualization
