# API Reference

This document provides a complete reference for the TensorBoard Flight Plugin API.

## Python API

### FlightLogger

The main class for logging flight data to TensorBoard.

```python
from tensorboard_flight import FlightLogger
```

#### Constructor

```python
FlightLogger(log_dir: str, max_buffer_size: int = 1000, flush_secs: int = 120)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_dir` | str | required | Directory for TensorBoard event files |
| `max_buffer_size` | int | 1000 | Number of episodes to buffer before auto-flush |
| `flush_secs` | int | 120 | Auto-flush interval in seconds |

#### Methods

##### `log_flight_data()`

Log a single flight data point.

```python
def log_flight_data(
    timestamp: float,
    step: int,
    position: np.ndarray,      # [x, y, z] in meters (NED)
    orientation: Orientation,   # roll, pitch, yaw in degrees
    velocity: np.ndarray,      # [vx, vy, vz] in m/s (NED)
    angular_velocity: np.ndarray = None,
    telemetry: Telemetry = None,
    rl_metrics: RLMetrics = None,
    events: List[Event] = None
) -> None
```

##### `end_episode()`

Mark the end of an episode and flush data.

```python
def end_episode(
    success: bool = False,
    termination_reason: str = "unknown"
) -> None
```

##### `flush()`

Manually flush buffered data to disk.

```python
def flush() -> None
```

---

### FlightLoggerCallback

Stable-Baselines3 integration callback.

```python
from tensorboard_flight import FlightLoggerCallback
```

#### Constructor

```python
FlightLoggerCallback(
    logger: FlightLogger,
    log_every_n_episodes: int = 1,
    agent_id: str = "sb3_agent",
    verbose: int = 0
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `logger` | FlightLogger | required | FlightLogger instance |
| `log_every_n_episodes` | int | 1 | Log every N episodes |
| `agent_id` | str | "sb3_agent" | Agent identifier |
| `verbose` | int | 0 | Verbosity level |

---

### Data Structures

#### Orientation

```python
from tensorboard_flight.data.schema import Orientation

Orientation(
    roll: float,   # degrees, right wing down positive
    pitch: float,  # degrees, nose up positive
    yaw: float     # degrees, 0=North, 90=East
)
```

#### Telemetry

```python
from tensorboard_flight.data.schema import Telemetry

Telemetry(
    airspeed: float = 0.0,      # m/s
    altitude: float = 0.0,       # meters
    g_force: float = 1.0,        # G's
    throttle: float = 0.0,       # 0.0-1.0
    aoa: float = 0.0,            # degrees (angle of attack)
    aos: float = 0.0,            # degrees (angle of sideslip)
    heading: float = 0.0,        # degrees
    vertical_speed: float = 0.0, # m/s
    turn_rate: float = 0.0,      # deg/s
    bank_angle: float = 0.0,     # degrees
    aileron: float = None,       # -1.0 to 1.0
    elevator: float = None,      # -1.0 to 1.0
    rudder: float = None         # -1.0 to 1.0
)
```

#### RLMetrics

```python
from tensorboard_flight.data.schema import RLMetrics

RLMetrics(
    reward: float = 0.0,
    cumulative_reward: float = 0.0,
    action: List[float] = None,
    policy_logprob: float = None,
    value_estimate: float = None,
    advantage: float = None,
    entropy: float = None,
    reward_components: Dict[str, float] = None
)
```

---

## REST API

The plugin exposes the following REST endpoints under `/data/plugin/flight/`:

### GET /runs

List all runs containing flight data.

**Response:**
```json
{
  "runs": [
    {
      "run": "run_name",
      "tags": ["flight_episode"]
    }
  ]
}
```

### GET /episodes

List episodes for a specific run.

**Query Parameters:**
- `run` (required): Run name

**Response:**
```json
{
  "episodes": [
    {
      "episode_id": "uuid",
      "agent_id": "agent_name",
      "episode_number": 1,
      "total_steps": 500,
      "total_reward": 125.5,
      "success": true,
      "duration": 10.5,
      "step": 1,
      "wall_time": 1699500000.0
    }
  ]
}
```

### GET /episode_data

Get full trajectory data for an episode.

**Query Parameters:**
- `run` (required): Run name
- `episode_id` (required): Episode UUID

**Response:**
```json
{
  "episode_id": "uuid",
  "agent_id": "agent_name",
  "trajectory": [
    {
      "timestamp": 0.0,
      "step": 0,
      "position": [0, 0, -100],
      "orientation": {"roll": 0, "pitch": 0, "yaw": 90},
      "velocity": [50, 0, 0],
      "telemetry": {...},
      "rl_metrics": {...}
    }
  ]
}
```

### GET /export_acmi

Export episode as ACMI file (Tacview compatible).

**Query Parameters:**
- `run` (required): Run name
- `episode_id` (required): Episode UUID

**Response:** ACMI text file download

### GET /tags

Get available tags for a run.

**Query Parameters:**
- `run` (required): Run name

**Response:**
```json
{
  "tags": ["flight_episode", "flight_episode_v2"]
}
```

---

## Coordinate System

The plugin uses NED (North-East-Down) coordinates:

```
      North (+X)
         ↑
         │
West ←───┼───→ East (+Y)
         │
         ↓
      (Down +Z into page)
```

| Axis | Direction | Unit |
|------|-----------|------|
| X | North | meters |
| Y | East | meters |
| Z | Down | meters |

### Orientation Convention

| Angle | Positive Direction | Zero Reference |
|-------|-------------------|----------------|
| Roll | Right wing down | Wings level |
| Pitch | Nose up | Level flight |
| Yaw | Clockwise | North |
