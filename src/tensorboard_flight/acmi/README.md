# ACMI Module - Quick Reference

The ACMI module provides complete bidirectional support for the ACMI flight recording format with Custom Agent Metadata (CAM) extensions for RL/AI data.

## 30-Second Integration

### Add ACMI Export to Your Training

```python
# Before (standard logger)
from tensorboard_flight import FlightLogger
logger = FlightLogger("runs/training")

# After (with ACMI export)
from tensorboard_flight.acmi import ACMILogger
logger = ACMILogger("runs/training", enable_acmi_export=True)

# That's it! ACMI files auto-generated in runs/training/acmi/
```

### Import ACMI Files

```bash
# Command line
python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/imported

# Python
from tensorboard_flight.acmi import import_acmi
import_acmi("mission.txt.acmi", "runs/imported")
```

## Module Structure

```
acmi/
├── __init__.py          # Public API exports
├── cam_schema.py        # CAM key definitions + encoder/decoder
├── geo_utils.py         # Coordinate conversions
├── parser.py            # ACMI file parser
├── writer.py            # ACMI file writer
├── converter.py         # Bidirectional FlightEpisode ↔ ACMI
├── logger.py            # ACMILogger (FlightLogger + ACMI export)
├── cli.py               # Command-line tools
└── README.md            # This file
```

## Core Classes

### ACMILogger
Drop-in replacement for `FlightLogger` with automatic ACMI export.

```python
from tensorboard_flight.acmi import ACMILogger

logger = ACMILogger(
    log_dir="runs/training",
    enable_acmi_export=True,        # Enable ACMI
    acmi_export_interval=10,        # Export every 10th episode
)

# Use exactly like FlightLogger
logger.start_episode("agent")
logger.log_flight_data(...)
logger.end_episode(success=True)
```

### ACMIConverter
Bidirectional converter between ACMI and FlightEpisode.

```python
from tensorboard_flight.acmi import ACMIConverter

converter = ACMIConverter()

# ACMI → FlightEpisode
episodes = converter.acmi_to_episodes("input.txt.acmi")

# FlightEpisode → ACMI
converter.episode_to_acmi(episode, "output.txt.acmi")
```

### ACMIParser
Low-level ACMI file parser.

```python
from tensorboard_flight.acmi.parser import ACMIParser

parser = ACMIParser()
data = parser.parse_file("mission.txt.acmi")

print(f"Objects: {len(data['objects'])}")
print(f"Events: {len(data['events'])}")
```

### ACMIWriter
Low-level ACMI file writer.

```python
from tensorboard_flight.acmi.writer import ACMIWriter

writer = ACMIWriter()
writer.write_episode(episode, "output.txt.acmi")
```

## CAM Schema

### Encoder/Decoder

```python
from tensorboard_flight.acmi.cam_schema import CAMEncoder, CAMDecoder

# Encode RL metrics to CAM properties
encoder = CAMEncoder()
props = encoder.encode_rl_metrics(rl_metrics)
# Returns: {'Agent.Reward.Instant': 1.5, 'Agent.Action.0': 0.1, ...}

# Decode CAM properties to RL metrics dict
decoder = CAMDecoder()
metrics = decoder.decode_rl_metrics(acmi_props)
# Returns: {'reward': 1.5, 'action': [0.1, ...], ...}
```

### Key Definitions

```python
from tensorboard_flight.acmi.cam_schema import CAMKeys

print(CAMKeys.REWARD_INSTANT)  # "Agent.Reward.Instant"
print(CAMKeys.ACTION_PREFIX)   # "Agent.Action"
print(CAMKeys.VALUE)           # "Agent.Value"
```

## Coordinate Utilities

```python
from tensorboard_flight.acmi.geo_utils import (
    geodetic_to_cartesian,
    cartesian_to_geodetic,
    compute_velocity_from_airspeed,
)

# Geodetic → Cartesian (ENU)
x, y, z = geodetic_to_cartesian(
    lat=34.91, lon=-117.88, alt=1000,
    ref_point=(34.90, -117.88, 700)
)

# Cartesian → Geodetic
lat, lon, alt = cartesian_to_geodetic(
    position=(100, 200, 300),
    ref_point=(34.90, -117.88, 700)
)

# Compute velocity from airspeed + orientation
vx, vy, vz = compute_velocity_from_airspeed(
    airspeed=50.0,
    pitch=5.0,   # degrees
    yaw=90.0,    # degrees
)
```

## CLI Tools

All commands use: `python -m tensorboard_flight.acmi <command>`

### Import

```bash
# Single file
python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/imported

# Batch import
python -m tensorboard_flight.acmi batch-import acmi_dir/ --output runs/all

# With custom prefix
python -m tensorboard_flight.acmi import file.txt.acmi --output runs/data --prefix dcs
```

### Inspect

```bash
# Show file info
python -m tensorboard_flight.acmi info mission.txt.acmi

# Validate format
python -m tensorboard_flight.acmi validate mission.txt.acmi

# Test roundtrip
python -m tensorboard_flight.acmi convert mission.txt.acmi
```

### Help

```bash
# Show all commands
python -m tensorboard_flight.acmi --help

# Command-specific help
python -m tensorboard_flight.acmi import --help
```

## Examples

### Example 1: SB3 Integration

```python
from stable_baselines3 import PPO
from tensorboard_flight.acmi import ACMILogger
from tensorboard_flight.callbacks import FlightLoggerCallback

# Create logger with ACMI export
logger = ACMILogger(
    log_dir="runs/ppo",
    enable_acmi_export=True,
    acmi_export_interval=50,
)

# Create callback
callback = FlightLoggerCallback(logger, log_every_n_episodes=5)

# Train
model = PPO("MlpPolicy", env, tensorboard_log="runs/ppo")
model.learn(total_timesteps=1000000, callback=callback)

# Results in runs/ppo/acmi/episode_*.txt.acmi
```

### Example 2: Compare RL Agent vs Human

```python
from tensorboard_flight.acmi import import_acmi, ACMILogger

# Import human pilot ACMI from DCS
import_acmi("human_dcs_flight.txt.acmi", "runs/comparison")

# Train RL agent in same directory
logger = ACMILogger("runs/comparison")
# ... training ...

# View both in TensorBoard Flight tab
# $ tensorboard --logdir runs/comparison
```

### Example 3: Dataset Creation

```bash
# Collect ACMI files from multiple sources
mkdir dataset/acmi
cp dcs_missions/*.txt.acmi dataset/acmi/
cp tacview_exports/*.txt.acmi dataset/acmi/

# Batch import
python -m tensorboard_flight.acmi batch-import dataset/acmi --output runs/dataset

# Now use for analysis, imitation learning, etc.
```

## Testing

Run tests:

```bash
# All ACMI tests
python -m pytest tests/acmi/

# Specific test
python -m pytest tests/acmi/test_cam_schema.py

# With coverage
python -m pytest tests/acmi/ --cov=tensorboard_flight.acmi
```

## Performance

- **ACMI Export Overhead**: <1% of training time with `interval=10`
- **File Sizes**: ~10-50 KB per 10-second episode (text format)
- **Parsing Speed**: ~1000 timesteps/second
- **Lossless Roundtrip**: All CAM metadata preserved

## Compatibility

- **ACMI Version**: 2.2 (text format)
- **Tacview**: All versions (CAM fields gracefully ignored)
- **DCS World**: Import/export compatible
- **Falcon BMS**: Import compatible
- **IL-2 Sturmovik**: Import compatible

## Limitations

- Geodetic conversion uses flat-earth approximation (accurate for <100km areas)
- Binary ACMI format not yet supported (use text format)
- Multi-agent ACMI exports each agent as separate file

## Advanced Usage

### Custom Reference Point

```python
from tensorboard_flight.acmi import ACMILogger

logger = ACMILogger("runs/training", enable_acmi_export=True)

# Set custom reference (e.g., your airfield)
logger.set_acmi_reference_point(
    lat=37.4099,   # Moffett Field
    lon=-122.0643,
    alt=11.0,
)
```

### Manual Episode Export

```python
from tensorboard_flight.acmi import ACMIConverter

converter = ACMIConverter()

# Export specific episode
converter.episode_to_acmi(best_episode, "best.txt.acmi")

# With custom reference
converter = ACMIConverter(reference_point=(lat, lon, alt))
converter.episode_to_acmi(episode, "output.txt.acmi")
```

### Low-Level Parsing

```python
from tensorboard_flight.acmi.parser import ACMIParser

parser = ACMIParser()
data = parser.parse_file("mission.txt.acmi")

# Access parsed data
for obj_id, states in data['objects'].items():
    print(f"Object {obj_id}: {len(states)} states")
    for state in states:
        if 'Agent.Reward.Instant' in state:
            print(f"  Reward: {state['Agent.Reward.Instant']}")
```

## Further Reading

- [Full ACMI Documentation](../../../docs/ACMI_SUPPORT.md)
- [ACMI 2.2 Specification](https://www.tacview.net/documentation/acmi/en/)
- [CAM Addendum Spec](./cam_schema.py)
- [Example Integration](../../../examples/acmi_integration.py)

## Support

For issues or questions:
1. Check [Full Documentation](../../../docs/ACMI_SUPPORT.md)
2. Run validation: `python -m tensorboard_flight.acmi validate file.txt.acmi`
3. Open issue on GitHub with sample file and error message
