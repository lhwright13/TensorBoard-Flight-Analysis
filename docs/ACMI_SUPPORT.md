# ACMI Support with Custom Agent Metadata (CAM)

The TensorBoard Flight Plugin now includes full support for the ACMI file format with Custom Agent Metadata (CAM) extensions for RL/AI data.

## Overview

**ACMI (Air Combat Maneuvering Instrumentation)** is the industry-standard flight recording format used by:
- Tacview (professional flight analysis software)
- DCS World (Digital Combat Simulator)
- Falcon BMS
- IL-2 Sturmovik
- Many other flight simulators and analysis tools

**CAM (Custom Agent Metadata)** is our extension that embeds RL/AI-specific metadata (rewards, actions, values, etc.) into ACMI files while maintaining full backward compatibility with standard ACMI viewers.

## Key Features

**Bidirectional Conversion**: ACMI ↔ TensorBoard with lossless RL metadata
**Backward Compatible**: ACMI files work in Tacview (CAM fields ignored)
**Drop-in Integration**: Use `ACMILogger` instead of `FlightLogger`
**CLI Tools**: Import/export from command line
**Batch Processing**: Convert entire directories of ACMI files

---

## Quick Start

### 1. Automatic ACMI Export During Training

```python
from tensorboard_flight.acmi import ACMILogger

# Drop-in replacement for FlightLogger
logger = ACMILogger(
    log_dir="runs/training",
    enable_acmi_export=True,        # Enable ACMI generation
    acmi_dir="runs/training/acmi",  # Where to save .txt.acmi files
    acmi_export_interval=10,        # Export every 10th episode
)

# Use exactly like FlightLogger
logger.start_episode("my_agent")
logger.log_flight_data(
    step=0,
    agent_id="my_agent",
    position=(x, y, z),
    orientation=(roll, pitch, yaw),
    velocity=(vx, vy, vz),
    telemetry={...},
    rl_metrics={...},
)
logger.end_episode(success=True)

# ACMI files automatically created in runs/training/acmi/
# - episode_0000.txt.acmi
# - episode_0010.txt.acmi
# - episode_0020.txt.acmi
```

### 2. Import ACMI Files to TensorBoard

```python
from tensorboard_flight.acmi import import_acmi

# Import single file
import_acmi("dcs_mission.txt.acmi", output_dir="runs/dcs_data")

# Import entire directory
from tensorboard_flight.acmi import batch_import_acmi
batch_import_acmi("acmi_files/", output_dir="runs/all_missions")

# View in TensorBoard
# $ tensorboard --logdir runs/dcs_data
# Navigate to "Flight" tab
```

### 3. Export TensorBoard Episode to ACMI

```python
from tensorboard_flight.acmi import ACMIConverter

converter = ACMIConverter()

# Export specific episode
converter.episode_to_acmi(episode, "best_flight.txt.acmi")

# Now share with colleagues or view in Tacview!
```

---

## Integration with Stable-Baselines3

### Option 1: ACMILogger with Callback

```python
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CallbackList
from tensorboard_flight.acmi import ACMILogger
from tensorboard_flight.callbacks import FlightLoggerCallback

# Create ACMI-enabled logger
logger = ACMILogger(
    log_dir="runs/ppo_training",
    enable_acmi_export=True,
    acmi_export_interval=50,  # Export every 50 episodes
)

# Create callback
flight_callback = FlightLoggerCallback(
    logger=logger,
    log_every_n_episodes=5,  # Log every 5 episodes
    agent_id="ppo_agent",
)

# Train
model = PPO("MlpPolicy", env, tensorboard_log="runs/ppo_training")
model.learn(total_timesteps=1000000, callback=flight_callback)

# Results:
# - TensorBoard logs: runs/ppo_training/
# - ACMI files: runs/ppo_training/acmi/episode_*.txt.acmi
```

### Option 2: Manual Export After Training

```python
from tensorboard_flight import FlightLogger
from tensorboard_flight.acmi import ACMIConverter

# Train with regular FlightLogger
logger = FlightLogger("runs/training")
# ... training happens ...
logger.close()

# Later, export specific episodes to ACMI
converter = ACMIConverter()

# Export best performing episodes
for episode_id in best_episode_ids:
    # Read from TensorBoard logs (requires custom code)
    episode = read_episode_from_logs("runs/training", episode_id)
    converter.episode_to_acmi(episode, f"best_{episode_id}.txt.acmi")
```

---

## Command-Line Tools

### Import ACMI

```bash
# Import single file
python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/imported

# Batch import directory
python -m tensorboard_flight.acmi batch-import acmi_files/ --output runs/all

# With custom agent prefix
python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/test --prefix dcs
```

### Inspect ACMI Files

```bash
# Show file info
python -m tensorboard_flight.acmi info mission.txt.acmi

# Validate format
python -m tensorboard_flight.acmi validate mission.txt.acmi

# Test roundtrip conversion
python -m tensorboard_flight.acmi convert mission.txt.acmi
```

---

## CAM Metadata Specification

The Custom Agent Metadata (CAM) addendum defines the following key namespace:

### Core RL Metrics

| CAM Key | Type | Description |
|---------|------|-------------|
| `Agent.Reward.Instant` | float | Step reward |
| `Agent.Reward.Cum` | float | Cumulative episode reward |
| `Agent.Action.N` | float | Action component N |
| `Agent.Value` | float | Value function estimate |
| `Agent.LogProb` | float | Policy log probability |
| `Agent.Advantage` | float | Advantage estimate (A2C/PPO) |
| `Agent.Entropy` | float | Policy entropy |

### Reward Components (Multi-Objective)

```
Agent.Reward.Tracking = 0.8
Agent.Reward.Stability = 0.3
Agent.Reward.Efficiency = -0.1
```

### Control Data

| CAM Key | Type | Description |
|---------|------|-------------|
| `Agent.Control.Aileron` | float | Aileron input [-1, 1] |
| `Agent.Control.Elevator` | float | Elevator input [-1, 1] |
| `Agent.Control.Rudder` | float | Rudder input [-1, 1] |
| `Agent.AngularVel.P` | float | Roll rate (rad/s) |
| `Agent.AngularVel.Q` | float | Pitch rate (rad/s) |
| `Agent.AngularVel.R` | float | Yaw rate (rad/s) |
| `Agent.GForce` | float | G-force magnitude |

### Episode Metadata

| CAM Key | Type | Description |
|---------|------|-------------|
| `Agent.EpisodeID` | string | Unique episode identifier |
| `Agent.EpisodeNum` | int | Episode number |
| `Agent.Success` | bool | Success flag |
| `Agent.TermReason` | string | Termination reason |
| `Agent.Tags` | string | Comma-separated tags |
| `Agent.Config.*` | any | Flattened config dict |

### Example ACMI with CAM

```
FileType=text/acmi/tacview
FileVersion=2.2

0,ReferenceTime=2025-10-23T00:00:00Z
0,Title="RL Training Episode 142"
0,Author="TensorBoard Flight Plugin"

#0.0
a01,Type=Air+FixedWing,Name="ppo_lstm_agent",Coalition=Blue,
    Agent.EpisodeID="episode_142",Agent.EpisodeNum=142,
    Agent.Tags="training,phase2"

#0.02
a01,T=-117.88|34.91|1000.0|0.0|5.0|90.0,IAS=50.0,Throttle=0.7,
    Agent.GForce=1.02,
    Agent.AngularVel.P=0.01,Agent.AngularVel.Q=0.02,Agent.AngularVel.R=0.00,
    Agent.Control.Aileron=0.12,Agent.Control.Elevator=-0.05,Agent.Control.Rudder=0.02,
    Agent.Reward.Instant=1.23,Agent.Reward.Cum=1.23,
    Agent.Action.0=0.12,Agent.Action.1=-0.05,Agent.Action.2=0.02,Agent.Action.3=0.70,
    Agent.Value=142.5,Agent.LogProb=-1.2,
    Agent.Reward.Tracking=0.80,Agent.Reward.Stability=0.30

#10.0
a01,Agent.Success=true,Agent.TermReason="completed"

#10.1
-a01
```

---

## Coordinate Systems

### TensorBoard Flight Plugin
- **Position**: Cartesian (x, y, z) in meters, East-North-Up (ENU)
- **Origin**: Configurable reference point

### ACMI Format
- **Position**: Geodetic (latitude, longitude, altitude MSL)
- **Format**: `T=Lon|Lat|Alt|Roll|Pitch|Yaw`

The converter handles automatic transformation using flat-earth approximation (suitable for <100km areas).

### Custom Reference Point

```python
from tensorboard_flight.acmi import ACMILogger

logger = ACMILogger("runs/training", enable_acmi_export=True)

# Set custom reference (e.g., your local airfield)
logger.set_acmi_reference_point(
    lat=37.4099,   # Moffett Field, CA
    lon=-122.0643,
    alt=11.0,      # meters MSL
)
```

---

## Viewing ACMI Files

### In TensorBoard (This Plugin)
```bash
# Import ACMI
python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/view

# Launch TensorBoard
tensorboard --logdir runs/view

# Navigate to "Flight" tab
# - Interactive 3D viewer
# - Playback controls
# - RL metrics display
```

### In Tacview (Professional Tool)
```bash
# Open ACMI file
tacview episode_0100.txt.acmi

# Features:
# - Advanced 3D visualization
# - Flight path analysis
# - Performance metrics
# - Export to video

# Note: CAM fields (Agent.*) are ignored but file plays normally
```

---

## Use Cases

### 1. Compare RL Agent vs Human Pilot
```python
# Import human flight from DCS/Tacview
import_acmi("human_pilot.txt.acmi", "runs/comparison")

# Log RL agent to same directory
logger = ACMILogger("runs/comparison", enable_acmi_export=False)
# ... train agent ...

# View both in TensorBoard side-by-side
```

### 2. Share Training Results
```python
# Export best episodes to ACMI
converter = ACMIConverter()
for episode in best_episodes:
    converter.episode_to_acmi(episode, f"results/{episode.episode_id}.txt.acmi")

# Share .txt.acmi files with colleagues
# They can:
# - View in Tacview (professional analysis)
# - Import to their own TensorBoard
# - Archive in standard format
```

### 3. Create Training Datasets
```bash
# Collect ACMI files from multiple sources
# - DCS World missions
# - Real flight data (if available)
# - Other RL agents

# Batch import
python -m tensorboard_flight.acmi batch-import dataset/acmi --output runs/dataset

# Use for imitation learning, comparison, analysis
```

### 4. Curriculum Learning
```python
# Phase 1: Train on simple scenarios
logger = ACMILogger("runs/phase1", enable_acmi_export=True)
# ... train ...

# Phase 2: Import best from phase 1 as demonstrations
import_acmi("runs/phase1/acmi/best.txt.acmi", "runs/phase2")
# ... continue training with demonstrations ...
```

---

## API Reference

### ACMILogger

```python
class ACMILogger(FlightLogger):
    """Extended FlightLogger with automatic ACMI export."""

    def __init__(
        self,
        log_dir: str,
        enable_acmi_export: bool = False,
        acmi_dir: Optional[str] = None,
        acmi_export_interval: int = 1,
        acmi_prefix: str = "episode",
        **kwargs
    ):
        """
        Args:
            log_dir: TensorBoard log directory
            enable_acmi_export: Auto-export episodes to ACMI
            acmi_dir: ACMI output directory (default: log_dir/acmi)
            acmi_export_interval: Export every N episodes
            acmi_prefix: Filename prefix
        """
```

### ACMIConverter

```python
class ACMIConverter:
    """Bidirectional ACMI ↔ FlightEpisode converter."""

    def acmi_to_episodes(self, acmi_file: str) -> List[FlightEpisode]:
        """Import ACMI file to FlightEpisodes."""

    def episode_to_acmi(self, episode: FlightEpisode, output_file: str):
        """Export FlightEpisode to ACMI file."""
```

### Convenience Functions

```python
def import_acmi(acmi_file: str, output_dir: str) -> int:
    """Import ACMI to TensorBoard logs."""

def batch_import_acmi(acmi_dir: str, output_dir: str) -> int:
    """Batch import directory of ACMI files."""

def export_to_acmi(logdir: str, output_file: str, episode_id: str) -> bool:
    """Export TensorBoard episode to ACMI."""
```

---

## Troubleshooting

### Issue: Coordinate mismatch after roundtrip
**Solution**: Check reference point. Geodetic conversion uses flat-earth approximation for areas <100km. For larger areas, coordinates may drift.

```python
# Set explicit reference point
converter = ACMIConverter(reference_point=(lat, lon, alt))
```

### Issue: Missing CAM metadata after import
**Check**: Original ACMI file may not have CAM fields. Standard ACMI from simulators won't have RL metrics - that's expected. Default values will be used.

### Issue: ACMI won't open in Tacview
**Solution**: Validate format first:
```bash
python -m tensorboard_flight.acmi validate file.txt.acmi
```

Common issues:
- Missing required header lines
- Incorrect timestamp format
- Invalid coordinate values

### Issue: Large file sizes
**Solution**: ACMI files can be compressed:
```bash
# Compress with gzip
gzip episode_0100.txt.acmi
# Creates: episode_0100.txt.acmi.gz

# Tacview can read .gz files directly
```

---

## Performance Notes

- ACMI export adds minimal overhead (<1% training time with `interval=10`)
- File sizes: ~10-50 KB per 10-second episode (uncompressed)
- Parsing speed: ~1000 timesteps/second on modern hardware
- Batch import: Processes files in parallel when possible

---

## Future Enhancements

Planned features:
- [ ] Binary ACMI format support (smaller files)
- [ ] Direct ZIP/7z compression
- [ ] Multi-agent ACMI files (single file, multiple objects)
- [ ] Real-time streaming to Tacview
- [ ] Advanced geodetic conversion (WGS84 ellipsoid)
- [ ] ACMI 2.3 format support

---

## References

- [ACMI 2.2 Specification](https://www.tacview.net/documentation/acmi/en/)
- [Tacview](https://www.tacview.net/)
- [CAM Addendum Spec](../src/tensorboard_flight/acmi/cam_schema.py)

---

## License

This ACMI implementation is part of the TensorBoard Flight Plugin and follows the same license.

The CAM addendum is designed to be backward-compatible and does not modify the core ACMI specification.
