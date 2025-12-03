"""TensorBoard Flight Visualization Plugin

A TensorBoard plugin for visualizing and analyzing flight trajectories
from reinforcement learning agents.

Features:
- Log flight trajectories during RL training
- Visualize 3D flight paths in TensorBoard
- Export/import ACMI format (Tacview compatible)
- Full CAM (Custom Agent Metadata) support for RL data
- Integration with Stable-Baselines3

Quick Start:
    # Basic logging
    >>> from tensorboard_flight import FlightLogger
    >>> logger = FlightLogger("runs/training")
    >>> logger.start_episode("my_agent")
    >>> logger.log_flight_data(...)
    >>> logger.end_episode(success=True)

    # With ACMI export
    >>> from tensorboard_flight.acmi import ACMILogger
    >>> logger = ACMILogger("runs/training", enable_acmi_export=True)
    >>> # Automatically creates .txt.acmi files!

    # Import ACMI files
    >>> from tensorboard_flight.acmi import import_acmi
    >>> import_acmi("mission.txt.acmi", "runs/imported")
"""

__version__ = "0.1.0"

from tensorboard_flight.logger import FlightLogger
from tensorboard_flight.data.schema import (
    FlightDataPoint,
    FlightEpisode,
    Orientation,
    Telemetry,
    RLMetrics,
    Event,
)

# ACMI support (optional import)
try:
    from tensorboard_flight.acmi import (
        ACMILogger,
        import_acmi,
        export_to_acmi,
        ACMIConverter,
    )
    __acmi_available__ = True
except ImportError:
    __acmi_available__ = False

__all__ = [
    "FlightLogger",
    "FlightDataPoint",
    "FlightEpisode",
    "Orientation",
    "Telemetry",
    "RLMetrics",
    "Event",
]

if __acmi_available__:
    __all__.extend([
        "ACMILogger",
        "import_acmi",
        "export_to_acmi",
        "ACMIConverter",
    ])
