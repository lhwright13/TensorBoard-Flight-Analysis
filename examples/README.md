# Examples

This directory contains example scripts demonstrating how to use the TensorBoard Flight Plugin.

## Quick Start: Dogfight Demo

The repository includes pre-generated demo data showcasing a dynamic dogfight scenario with two aircraft:
- **Aggressor**: Pursuit strategy with aggressive maneuvering
- **Defender**: Evasion strategy with defensive maneuvers

```bash
# View the demo immediately (no setup required)
tensorboard --logdir ../example_data/dogfight

# Open http://localhost:6006 and navigate to the "Flight" tab
# Select both runs (aggressor & defender) to see both aircraft
```

### Regenerate Demo Data

```bash
# Generate fresh dogfight demo data
python generate_dogfight_demo.py

# Custom duration (default: 60 seconds)
python generate_dogfight_demo.py --duration 120
```

The dogfight scenario includes:
- 6 phases: approach, defensive break, pursuit curves, vertical fight, rolling scissors, separation
- Full telemetry: airspeed, altitude, G-force, bank angle, throttle, etc.
- RL metrics: reward, value estimates, action vectors
- Multi-agent comparison with different strategies

## Basic Logging Example

`basic_logging.py` - Demonstrates basic FlightLogger API with simulated circular flight.

```bash
# Install the plugin
pip install -e ..

# Run the example
python basic_logging.py

# View in TensorBoard
tensorboard --logdir runs/basic_example
```

## ACMI Integration Example

`acmi_integration.py` - Shows how to use ACMILogger for automatic ACMI file export during training.

```bash
python acmi_integration.py

# Creates both TensorBoard logs AND .acmi files for Tacview
```

## Example Scripts

| Script | Description |
|--------|-------------|
| `generate_dogfight_demo.py` | Multi-agent combat scenario with pursuit/evasion |
| `basic_logging.py` | Simple FlightLogger usage with circular trajectory |
| `acmi_integration.py` | ACMI export for Tacview compatibility |
