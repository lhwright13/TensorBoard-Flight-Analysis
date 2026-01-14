# Configuration Guide

This document describes all configuration options for the TensorBoard Flight Plugin.

## FlightLogger Configuration

### Basic Setup

```python
from tensorboard_flight import FlightLogger

logger = FlightLogger(
    log_dir="runs/my_experiment",
    max_buffer_size=1000,
    flush_secs=120
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_dir` | str | **required** | Directory where TensorBoard event files are written |
| `max_buffer_size` | int | 1000 | Number of episodes to buffer in memory before auto-flushing to disk |
| `flush_secs` | int | 120 | Automatic flush interval in seconds |

### Buffer Management

The logger buffers episodes in memory for performance. Data is written to disk when:

1. `max_buffer_size` episodes are buffered
2. `flush_secs` seconds have elapsed since last flush
3. `flush()` is called manually
4. `end_episode()` is called

**Recommendation:** For long training runs, use default settings. For debugging, set `max_buffer_size=1` for immediate writes.

---

## ACMI Logger Configuration

### Basic Setup

```python
from tensorboard_flight.acmi import ACMILogger

logger = ACMILogger(
    log_dir="runs/my_experiment",
    enable_acmi_export=True,
    acmi_dir="acmi_exports",
    acmi_export_interval=10,
    acmi_prefix="episode",
    reference_point=(34.9054, -117.8839, 700.0)
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_acmi_export` | bool | False | Enable automatic ACMI file generation |
| `acmi_dir` | str | None | Directory for ACMI files (defaults to `log_dir/acmi`) |
| `acmi_export_interval` | int | 1 | Export every N episodes |
| `acmi_prefix` | str | "episode" | Filename prefix for ACMI files |
| `reference_point` | tuple | (0, 0, 0) | Geographic reference point (lat, lon, alt) |

### Reference Point

The reference point converts local NED coordinates to geodetic (lat/lon/alt) for ACMI compatibility:

```python
# Edwards AFB, California
reference_point = (34.9054, -117.8839, 700.0)  # (lat, lon, alt_meters)

# Custom location
reference_point = (latitude, longitude, altitude_msl)
```

---

## Stable-Baselines3 Callback Configuration

### Basic Setup

```python
from tensorboard_flight import FlightLogger, FlightLoggerCallback

logger = FlightLogger("runs/sb3_training")
callback = FlightLoggerCallback(
    logger=logger,
    log_every_n_episodes=10,
    agent_id="ppo_agent",
    verbose=1
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `logger` | FlightLogger | **required** | FlightLogger instance for data storage |
| `log_every_n_episodes` | int | 1 | Only log every N episodes (reduces data volume) |
| `agent_id` | str | "sb3_agent" | Identifier for this agent in multi-agent scenarios |
| `verbose` | int | 0 | Verbosity level (0=silent, 1=progress, 2=debug) |

### Data Extraction

The callback expects certain keys in the environment's `info` dict:

```python
info = {
    "position": np.array([x, y, z]),        # NED coordinates
    "orientation": {"roll": r, "pitch": p, "yaw": y},
    "velocity": np.array([vx, vy, vz]),
    "telemetry": {...},  # Optional
}
```

---

## Frontend Configuration

### 3D Model

The aircraft model can be customized in `Aircraft.tsx`:

```typescript
// Model path (relative to plugin static directory)
const MODEL_PATH = '/data/plugin/flight/static/models/fighter_jet.glb';

// Scale factor
const MODEL_SCALE = 0.02;

// Orientation correction (radians)
rotation={[-Math.PI / 2, 0, Math.PI]}
```

### Playback Settings

Controlled via the Zustand store in `store.ts`:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `playbackSpeed` | number | 1.0 | Playback speed multiplier (0.25x to 8x) |
| `showTrail` | boolean | true | Show trajectory trail |
| `trailLength` | number | 100 | Number of trail points |
| `trailColorMode` | string | "speed" | Trail color mode: "speed", "altitude", "reward" |
| `cameraLocked` | boolean | false | Lock camera to follow aircraft |

---

## TensorBoard Launch Options

### Basic Launch

```bash
tensorboard --logdir=runs/ --port=6006
```

### With Flight Plugin

The plugin is automatically loaded when installed. Access at:
```
http://localhost:6006/#flight
```

### Multiple Runs

```bash
tensorboard --logdir=runs/ --logdir_spec=exp1:runs/exp1,exp2:runs/exp2
```

---

## Environment Variables

Currently, the plugin does not use environment variables. All configuration is done via Python API parameters.

## Performance Tuning

### For Large Training Runs

```python
logger = FlightLogger(
    log_dir="runs/large_experiment",
    max_buffer_size=5000,    # Larger buffer, less frequent writes
    flush_secs=300           # 5 minute flush interval
)

callback = FlightLoggerCallback(
    logger=logger,
    log_every_n_episodes=100  # Only log every 100th episode
)
```

### For Debugging

```python
logger = FlightLogger(
    log_dir="runs/debug",
    max_buffer_size=1,       # Immediate flush
    flush_secs=10
)

callback = FlightLoggerCallback(
    logger=logger,
    log_every_n_episodes=1,  # Log every episode
    verbose=2                # Full debug output
)
```
