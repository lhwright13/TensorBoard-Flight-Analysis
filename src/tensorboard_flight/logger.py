"""FlightLogger for logging flight trajectory data to TensorBoard."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from tensorboard.compat.proto.summary_pb2 import Summary
from tensorboard.compat.proto.event_pb2 import Event as TBEvent
from tensorboard.summary.writer.event_file_writer import EventFileWriter

from tensorboard_flight.data.schema import (
    FlightDataPoint,
    FlightEpisode,
    Orientation,
    Telemetry,
    RLMetrics,
    Event,
)


class FlightLogger:
    """Logger for flight trajectory data in TensorBoard format.

    This class provides an easy-to-use API for logging flight data during
    RL training. Data is buffered and periodically written to TensorBoard
    event files.

    Example:
        >>> logger = FlightLogger(log_dir="runs/experiment_1")
        >>> for step in range(1000):
        >>>     logger.log_flight_data(
        >>>         step=step,
        >>>         agent_id="ppo_agent",
        >>>         position=(x, y, z),
        >>>         orientation=(roll, pitch, yaw),
        >>>         velocity=(vx, vy, vz),
        >>>         telemetry={...},
        >>>         rl_metrics={...}
        >>>     )
        >>> logger.close()
    """

    def __init__(
        self,
        log_dir: Union[str, Path],
        max_buffer_size: int = 1000,
        flush_secs: int = 120,
    ):
        """Initialize FlightLogger.

        Args:
            log_dir: Directory for TensorBoard logs
            max_buffer_size: Flush buffer after this many steps
            flush_secs: Flush buffer after this many seconds
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.max_buffer_size = max_buffer_size
        self.flush_secs = flush_secs

        # Create event file writer
        self.writer = EventFileWriter(str(self.log_dir))

        # Buffer for current episode
        self.current_episode: Optional[List[FlightDataPoint]] = None
        self.episode_start_time: Optional[float] = None
        self.episode_number = 0
        self.current_agent_id: Optional[str] = None

        # Cumulative reward tracking
        self.cumulative_reward = 0.0

        # Last flush time
        self.last_flush_time = time.time()

    def start_episode(self, agent_id: str) -> None:
        """Start a new episode.

        Args:
            agent_id: Identifier for the agent/policy
        """
        if self.current_episode is not None:
            raise RuntimeError("Episode already in progress. Call end_episode() first.")

        self.current_episode = []
        self.episode_start_time = time.time()
        self.current_agent_id = agent_id
        self.cumulative_reward = 0.0

    def log_flight_data(
        self,
        step: int,
        agent_id: str,
        position: Tuple[float, float, float],
        orientation: Tuple[float, float, float],
        velocity: Tuple[float, float, float],
        telemetry: Dict[str, float],
        rl_metrics: Dict[str, Any],
        angular_velocity: Optional[Tuple[float, float, float]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Log a single timestep of flight data.

        Args:
            step: Episode step number
            agent_id: Agent identifier
            position: (x, y, z) position in meters
            orientation: (roll, pitch, yaw) in degrees
            velocity: (vx, vy, vz) in m/s
            telemetry: Dictionary of telemetry values
            rl_metrics: Dictionary of RL metrics (must include 'reward' and 'action')
            angular_velocity: (p, q, r) body rates in rad/s
            events: List of event dictionaries
            timestamp: Simulation time (defaults to step count)
        """
        # Auto-start episode if needed
        if self.current_episode is None:
            self.start_episode(agent_id)

        # Check agent consistency
        if agent_id != self.current_agent_id:
            raise ValueError(
                f"Agent ID mismatch: {agent_id} != {self.current_agent_id}. "
                "Call end_episode() before switching agents."
            )

        # Parse timestamp
        if timestamp is None:
            timestamp = float(step)

        # Update cumulative reward
        self.cumulative_reward += rl_metrics.get('reward', 0.0)

        # Create data structures
        orientation_obj = Orientation(
            roll=orientation[0],
            pitch=orientation[1],
            yaw=orientation[2],
        )

        telemetry_obj = Telemetry(
            airspeed=telemetry.get('airspeed', 0.0),
            altitude=telemetry.get('altitude', 0.0),
            g_force=telemetry.get('g_force', 1.0),
            throttle=telemetry.get('throttle', 0.0),
            aoa=telemetry.get('aoa', 0.0),
            aos=telemetry.get('aos', 0.0),
            heading=telemetry.get('heading', 0.0),
            vertical_speed=telemetry.get('vertical_speed', 0.0),
            turn_rate=telemetry.get('turn_rate', 0.0),
            bank_angle=telemetry.get('bank_angle', orientation[0]),
            aileron=telemetry.get('aileron'),
            elevator=telemetry.get('elevator'),
            rudder=telemetry.get('rudder'),
        )

        rl_metrics_obj = RLMetrics(
            reward=rl_metrics['reward'],
            cumulative_reward=self.cumulative_reward,
            action=rl_metrics['action'] if isinstance(rl_metrics['action'], list) else list(rl_metrics['action']),
            policy_logprob=rl_metrics.get('policy_logprob'),
            value_estimate=rl_metrics.get('value_estimate'),
            advantage=rl_metrics.get('advantage'),
            entropy=rl_metrics.get('entropy'),
            reward_components=rl_metrics.get('reward_components'),
        )

        # Parse events
        events_obj = None
        if events:
            events_obj = [
                Event(
                    timestamp=e.get('timestamp', timestamp),
                    event_type=e.get('type', 'custom'),
                    severity=e.get('severity', 'info'),
                    message=e.get('message', ''),
                    metadata=e.get('metadata'),
                )
                for e in events
            ]

        # Create flight data point
        data_point = FlightDataPoint(
            timestamp=timestamp,
            step=step,
            position=np.array(position),
            orientation=orientation_obj,
            velocity=np.array(velocity),
            angular_velocity=np.array(angular_velocity if angular_velocity else [0.0, 0.0, 0.0]),
            telemetry=telemetry_obj,
            rl_metrics=rl_metrics_obj,
            events=events_obj,
        )

        # Add to buffer
        self.current_episode.append(data_point)

        # Check if we should flush
        if len(self.current_episode) >= self.max_buffer_size:
            self._maybe_flush()
        elif time.time() - self.last_flush_time > self.flush_secs:
            self._maybe_flush()

    def end_episode(
        self,
        success: bool = False,
        termination_reason: str = "unknown",
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """End the current episode and write to TensorBoard.

        Args:
            success: Whether the episode was successful
            termination_reason: Reason for episode termination
            config: Optional configuration dictionary
            tags: Optional list of tags for this episode
        """
        if self.current_episode is None:
            raise RuntimeError("No episode in progress. Call start_episode() first.")

        # Calculate episode duration
        duration = time.time() - self.episode_start_time

        # Create episode object
        episode = FlightEpisode(
            episode_id=f"{self.current_agent_id}_ep{self.episode_number}",
            agent_id=self.current_agent_id,
            episode_number=self.episode_number,
            start_time=self.episode_start_time,
            duration=duration,
            total_steps=len(self.current_episode),
            total_reward=self.cumulative_reward,
            success=success,
            termination_reason=termination_reason,
            trajectory=self.current_episode,
            config=config,
            tags=tags,
        )

        # Write to TensorBoard
        self._write_episode(episode)

        # Reset state
        self.current_episode = None
        self.episode_start_time = None
        self.cumulative_reward = 0.0
        self.episode_number += 1

    def log_episode(self, episode: FlightEpisode) -> None:
        """Log a complete episode at once.

        This is useful if you've already collected the full trajectory.

        Args:
            episode: Complete FlightEpisode object
        """
        self._write_episode(episode)
        self.episode_number += 1

    def _write_episode(self, episode: FlightEpisode) -> None:
        """Write episode data to TensorBoard event file.

        Args:
            episode: Episode to write
        """
        # Convert episode to JSON for storage
        # In the future, we'll use protobuf for efficiency
        episode_json = json.dumps(episode.to_dict())

        # Create summary with plugin metadata
        summary = Summary()
        value = summary.value.add()
        value.tag = f"flight/{episode.agent_id}/episode"

        # Create plugin metadata
        plugin_data = value.metadata.plugin_data
        plugin_data.plugin_name = "flight"
        plugin_data.content = episode_json.encode('utf-8')

        # Create event
        event = TBEvent(
            wall_time=time.time(),
            step=episode.episode_number,
            summary=summary,
        )

        # Write to file
        self.writer.add_event(event)
        self.writer.flush()
        self.last_flush_time = time.time()

    def _maybe_flush(self) -> None:
        """Flush data if buffer is full or timeout reached."""
        self.writer.flush()
        self.last_flush_time = time.time()

    def flush(self) -> None:
        """Force flush buffered data to disk."""
        if self.writer:
            self.writer.flush()
            self.last_flush_time = time.time()

    def close(self) -> None:
        """Close the logger and flush remaining data."""
        if self.current_episode is not None:
            # Auto-end episode with warning
            print(f"Warning: Ending incomplete episode with {len(self.current_episode)} steps")
            self.end_episode(termination_reason="logger_closed")

        if self.writer:
            self.writer.flush()
            self.writer.close()
