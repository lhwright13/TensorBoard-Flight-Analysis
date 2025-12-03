"""ACMI file format support with Custom Agent Metadata (CAM) for RL integration.

This module provides complete bidirectional conversion between TensorBoard Flight Plugin
format and ACMI 2.2 text format with CAM extensions for RL metadata.

Key Features:
- Import ACMI files (from DCS, Tacview, etc.) into TensorBoard
- Export RL training data to ACMI for viewing in Tacview
- Lossless roundtrip of RL metadata (rewards, actions, values)
- Full compatibility with standard ACMI viewers

Quick Start:
    # Import ACMI to TensorBoard
    >>> from tensorboard_flight.acmi import import_acmi
    >>> import_acmi("mission.txt.acmi", output_dir="runs/imported")

    # Export TensorBoard episode to ACMI
    >>> from tensorboard_flight.acmi import export_to_acmi
    >>> export_to_acmi("runs/training", episode_id="episode_42",
    ...                output_file="rl_flight.txt.acmi")

    # Use in training loop
    >>> from tensorboard_flight.acmi import ACMILogger
    >>> logger = ACMILogger("runs/training", enable_acmi_export=True)
    >>> # ... training happens, ACMI files auto-generated
"""

from .cam_schema import CAMKeys, CAMEncoder, CAMDecoder
from .geo_utils import (
    geodetic_to_cartesian,
    cartesian_to_geodetic,
    compute_velocity_from_airspeed,
)
from .parser import ACMIParser
from .writer import ACMIWriter
from .converter import ACMIConverter, import_acmi, export_to_acmi
from .logger import ACMILogger

__all__ = [
    # Core classes
    "ACMIParser",
    "ACMIWriter",
    "ACMIConverter",
    "ACMILogger",

    # CAM schema
    "CAMKeys",
    "CAMEncoder",
    "CAMDecoder",

    # Utilities
    "geodetic_to_cartesian",
    "cartesian_to_geodetic",
    "compute_velocity_from_airspeed",

    # High-level API
    "import_acmi",
    "export_to_acmi",
]
