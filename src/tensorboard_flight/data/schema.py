"""Data structures for flight trajectory data."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np


def _to_python_type(value: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, dict):
        return {k: _to_python_type(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_to_python_type(v) for v in value]
    return value


@dataclass
class Orientation:
    """Aircraft orientation in Euler angles (degrees)."""
    roll: float      # Bank angle: positive = right wing down
    pitch: float     # Nose up/down: positive = nose up
    yaw: float       # Heading: 0-360, 0=North, 90=East

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            "roll": _to_python_type(self.roll),
            "pitch": _to_python_type(self.pitch),
            "yaw": _to_python_type(self.yaw),
        }


@dataclass
class Telemetry:
    """Core flight telemetry data."""
    airspeed: float           # True airspeed (m/s)
    altitude: float           # Altitude MSL (meters)
    g_force: float            # G-loading on aircraft
    throttle: float           # Throttle position [0, 1]
    aoa: float                # Angle of attack (degrees)
    aos: float                # Angle of sideslip (degrees)
    heading: float            # Magnetic heading (degrees)
    vertical_speed: float     # Rate of climb (m/s)
    turn_rate: float          # Rate of turn (deg/s)
    bank_angle: float         # Roll angle (degrees)

    # Control surface positions (optional)
    aileron: Optional[float] = None   # [-1, 1]
    elevator: Optional[float] = None  # [-1, 1]
    rudder: Optional[float] = None    # [-1, 1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "airspeed": _to_python_type(self.airspeed),
            "altitude": _to_python_type(self.altitude),
            "g_force": _to_python_type(self.g_force),
            "throttle": _to_python_type(self.throttle),
            "aoa": _to_python_type(self.aoa),
            "aos": _to_python_type(self.aos),
            "heading": _to_python_type(self.heading),
            "vertical_speed": _to_python_type(self.vertical_speed),
            "turn_rate": _to_python_type(self.turn_rate),
            "bank_angle": _to_python_type(self.bank_angle),
        }
        if self.aileron is not None:
            result["aileron"] = _to_python_type(self.aileron)
        if self.elevator is not None:
            result["elevator"] = _to_python_type(self.elevator)
        if self.rudder is not None:
            result["rudder"] = _to_python_type(self.rudder)
        return result


@dataclass
class RLMetrics:
    """Reinforcement learning specific metrics."""
    reward: float                      # Step reward
    cumulative_reward: float           # Episode cumulative reward
    action: List[float]                # Action taken
    policy_logprob: Optional[float] = None    # Log probability of action
    value_estimate: Optional[float] = None    # Value function estimate
    advantage: Optional[float] = None         # Advantage estimate
    entropy: Optional[float] = None           # Policy entropy

    # Optional: reward components for multi-objective rewards
    reward_components: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "reward": _to_python_type(self.reward),
            "cumulative_reward": _to_python_type(self.cumulative_reward),
            "action": _to_python_type(self.action),
        }
        if self.policy_logprob is not None:
            result["policy_logprob"] = _to_python_type(self.policy_logprob)
        if self.value_estimate is not None:
            result["value_estimate"] = _to_python_type(self.value_estimate)
        if self.advantage is not None:
            result["advantage"] = _to_python_type(self.advantage)
        if self.entropy is not None:
            result["entropy"] = _to_python_type(self.entropy)
        if self.reward_components is not None:
            result["reward_components"] = _to_python_type(self.reward_components)
        return result


@dataclass
class Event:
    """Discrete event marker."""
    timestamp: float
    event_type: str           # "crash", "checkpoint", "timeout", "custom"
    severity: str             # "info", "warning", "error"
    message: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "timestamp": _to_python_type(self.timestamp),
            "event_type": self.event_type,
            "severity": self.severity,
            "message": self.message,
        }
        if self.metadata is not None:
            result["metadata"] = _to_python_type(self.metadata)
        return result


@dataclass
class FlightDataPoint:
    """Single timestep of flight data."""
    timestamp: float                    # Simulation time (seconds)
    step: int                           # Episode step number

    # Kinematic state
    position: np.ndarray                # [x, y, z] in world frame (meters)
    orientation: Orientation            # Aircraft attitude
    velocity: np.ndarray                # [vx, vy, vz] in world frame (m/s)
    angular_velocity: np.ndarray        # [p, q, r] body rates (rad/s)

    # Flight telemetry
    telemetry: Telemetry

    # RL metrics
    rl_metrics: RLMetrics

    # Optional events
    events: Optional[List[Event]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "timestamp": _to_python_type(self.timestamp),
            "step": int(self.step),
            "position": _to_python_type(self.position),
            "orientation": self.orientation.to_dict(),
            "velocity": _to_python_type(self.velocity),
            "angular_velocity": _to_python_type(self.angular_velocity),
            "telemetry": self.telemetry.to_dict(),
            "rl_metrics": self.rl_metrics.to_dict(),
        }
        if self.events is not None:
            result["events"] = [e.to_dict() for e in self.events]
        return result


@dataclass
class FlightEpisode:
    """Complete flight episode/trajectory."""
    episode_id: str                     # Unique identifier
    agent_id: str                       # Agent/policy identifier
    episode_number: int                 # Training episode number

    # Metadata
    start_time: float                   # Wall-clock start time
    duration: float                     # Episode duration (seconds)
    total_steps: int                    # Number of steps

    # Episode-level metrics
    total_reward: float
    success: bool
    termination_reason: str             # "success", "crash", "timeout", "other"

    # Trajectory data
    trajectory: List[FlightDataPoint] = field(default_factory=list)

    # Optional metadata
    config: Optional[Dict[str, Any]] = None  # Training config, hyperparams
    tags: Optional[List[str]] = None         # User-defined tags

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "episode_id": self.episode_id,
            "agent_id": self.agent_id,
            "episode_number": int(self.episode_number),
            "start_time": _to_python_type(self.start_time),
            "duration": _to_python_type(self.duration),
            "total_steps": int(self.total_steps),
            "total_reward": _to_python_type(self.total_reward),
            "success": bool(self.success),
            "termination_reason": self.termination_reason,
            "trajectory": [point.to_dict() for point in self.trajectory],
        }
        if self.config is not None:
            result["config"] = _to_python_type(self.config)
        if self.tags is not None:
            result["tags"] = self.tags
        return result
