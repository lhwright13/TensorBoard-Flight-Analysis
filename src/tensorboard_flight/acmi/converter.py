"""Bidirectional converter between ACMI format and FlightEpisode.

This module provides high-level functions for converting between ACMI files
and TensorBoard Flight Plugin format with full CAM metadata preservation.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from tensorboard_flight.data.schema import (
    FlightEpisode,
    FlightDataPoint,
    Orientation,
    Telemetry,
    RLMetrics,
    Event,
)
from tensorboard_flight import FlightLogger

from .parser import ACMIParser
from .writer import ACMIWriter
from .cam_schema import CAMDecoder
from .geo_utils import (
    geodetic_to_cartesian,
    compute_velocity_from_airspeed,
    compute_reference_point,
)


class ACMIConverter:
    """Bidirectional converter between ACMI and FlightEpisode format.

    Handles:
    - ACMI → FlightEpisode (import)
    - FlightEpisode → ACMI (export)
    - Full CAM metadata preservation for lossless roundtrip

    Example:
        >>> # Import ACMI
        >>> converter = ACMIConverter()
        >>> episodes = converter.acmi_to_episodes("mission.txt.acmi")
        >>>
        >>> # Export to ACMI
        >>> converter.episode_to_acmi(episode, "output.txt.acmi")
    """

    def __init__(self, reference_point: Optional[tuple] = None):
        """Initialize converter.

        Args:
            reference_point: (lat, lon, alt) for coordinate conversion.
                           If None, will be auto-computed from data.
        """
        self.reference_point = reference_point
        self.decoder = CAMDecoder()

    def acmi_to_episodes(self, acmi_file: str) -> List[FlightEpisode]:
        """Convert ACMI file to list of FlightEpisode objects.

        Each object in the ACMI file becomes a separate episode.

        Args:
            acmi_file: Path to .txt.acmi file

        Returns:
            List of FlightEpisode instances (one per object)

        Example:
            >>> converter = ACMIConverter()
            >>> episodes = converter.acmi_to_episodes("dcs_mission.txt.acmi")
            >>> print(f"Loaded {len(episodes)} episodes")
        """
        # Parse ACMI file
        parser = ACMIParser()
        data = parser.parse_file(acmi_file)

        # Convert each object to an episode
        episodes = []
        for obj_id, states in data['objects'].items():
            if not states:
                continue

            # Get object name (prefer Name property)
            agent_id = states[0].get('Name', obj_id)

            # Convert object to episode
            episode = self._convert_object_to_episode(
                obj_id, agent_id, states, data['global']
            )
            episodes.append(episode)

        return episodes

    def episode_to_acmi(
        self,
        episode: FlightEpisode,
        output_file: str,
        reference_point: Optional[tuple] = None
    ):
        """Convert FlightEpisode to ACMI file.

        Args:
            episode: FlightEpisode instance to export
            output_file: Output .txt.acmi file path
            reference_point: Optional (lat, lon, alt) override

        Example:
            >>> converter = ACMIConverter()
            >>> converter.episode_to_acmi(episode, "rl_flight.txt.acmi")
        """
        ref_point = reference_point or self.reference_point
        writer = ACMIWriter(reference_point=ref_point)
        writer.write_episode(episode, output_file)

    def _convert_object_to_episode(
        self,
        obj_id: str,
        agent_id: str,
        states: List[Dict],
        global_props: Dict
    ) -> FlightEpisode:
        """Convert ACMI object states to FlightEpisode.

        Args:
            obj_id: Object ID from ACMI
            agent_id: Agent name
            states: List of state dicts (timestamped)
            global_props: Global ACMI properties

        Returns:
            FlightEpisode instance
        """
        # Auto-compute reference point if needed
        if self.reference_point is None:
            # Use first position
            first_lat = states[0].get('Latitude', 34.9)
            first_lon = states[0].get('Longitude', -117.9)
            first_alt = states[0].get('Altitude', 700.0)
            self.reference_point = (first_lat, first_lon, first_alt)

        # Extract episode metadata from first/last states
        episode_meta = self._extract_episode_metadata(states)

        # Convert each state to FlightDataPoint
        trajectory = []
        cumulative_reward = 0.0

        for i, state in enumerate(states):
            datapoint = self._convert_state_to_datapoint(
                i, state, cumulative_reward
            )
            cumulative_reward = datapoint.rl_metrics.cumulative_reward
            trajectory.append(datapoint)

        # Create episode
        episode = FlightEpisode(
            episode_id=episode_meta.get('episode_id', f"acmi_{obj_id}"),
            agent_id=agent_id,
            episode_number=episode_meta.get('episode_number', 0),
            start_time=states[0]['timestamp'] if states else 0.0,
            trajectory=trajectory,
            total_steps=len(trajectory),
            total_reward=cumulative_reward,
            duration=states[-1]['timestamp'] - states[0]['timestamp'] if states else 0.0,
            success=episode_meta.get('success', True),
            termination_reason=episode_meta.get('termination_reason', 'completed'),
            config=episode_meta.get('config'),
            tags=episode_meta.get('tags'),
        )

        return episode

    def _convert_state_to_datapoint(
        self,
        step: int,
        state: Dict,
        prev_cumulative_reward: float
    ) -> FlightDataPoint:
        """Convert single ACMI state to FlightDataPoint.

        Args:
            step: Step number
            state: State dict from ACMI parser
            prev_cumulative_reward: Previous cumulative reward

        Returns:
            FlightDataPoint instance
        """
        # Extract position (geodetic → cartesian)
        lat = state.get('Latitude', 0.0)
        lon = state.get('Longitude', 0.0)
        alt = state.get('Altitude', 0.0)
        position = geodetic_to_cartesian(lat, lon, alt, self.reference_point)

        # Extract orientation
        roll = state.get('Roll', 0.0)
        pitch = state.get('Pitch', 0.0)
        yaw = state.get('Yaw', state.get('Heading', 0.0))
        orientation = Orientation(roll=roll, pitch=pitch, yaw=yaw)

        # Extract velocity (compute from IAS if not in CAM)
        airspeed = state.get('IAS', 0.0)
        velocity = compute_velocity_from_airspeed(airspeed, pitch, yaw)

        # Extract angular velocity (from CAM)
        angular_velocity = self.decoder.decode_angular_velocity(state)

        # Extract telemetry
        telemetry_dict = {
            'airspeed': airspeed,
            'altitude': alt,
            'g_force': self.decoder.decode_g_force(state),
            'throttle': state.get('Throttle', 0.5),
            'aoa': state.get('AOA', 0.0),
            'aos': state.get('AOS', 0.0),
            'heading': yaw,
            'vertical_speed': velocity[2],  # vz
            'turn_rate': state.get('TurnRate', 0.0),
            'bank_angle': roll,
        }

        # Add control surfaces from CAM
        controls = self.decoder.decode_control_surfaces(state)
        telemetry_dict.update(controls)

        telemetry = Telemetry(**telemetry_dict)

        # Extract RL metrics from CAM
        rl_metrics_dict = self.decoder.decode_rl_metrics(state)

        # Update cumulative reward
        instant_reward = rl_metrics_dict.get('reward', 0.0)
        if 'cumulative_reward' not in rl_metrics_dict:
            rl_metrics_dict['cumulative_reward'] = prev_cumulative_reward + instant_reward
        else:
            # Use CAM value if available
            rl_metrics_dict['cumulative_reward'] = rl_metrics_dict['cumulative_reward']

        rl_metrics = RLMetrics(**rl_metrics_dict)

        # Create datapoint
        datapoint = FlightDataPoint(
            step=step,
            timestamp=state['timestamp'],
            position=position,
            orientation=orientation,
            velocity=velocity,
            angular_velocity=angular_velocity,
            telemetry=telemetry,
            rl_metrics=rl_metrics,
        )

        return datapoint

    def _extract_episode_metadata(self, states: List[Dict]) -> Dict[str, Any]:
        """Extract episode metadata from first/last states.

        Args:
            states: List of state dicts

        Returns:
            Dictionary with episode metadata
        """
        metadata = {}

        # Extract from first state (episode start metadata)
        if states:
            first_meta = self.decoder.decode_episode_metadata(states[0])
            metadata.update(first_meta)

        # Extract from last state (termination metadata)
        if states:
            last_meta = self.decoder.decode_episode_metadata(states[-1])
            metadata.update(last_meta)

        return metadata


# High-level convenience functions

def import_acmi(acmi_file: str, output_dir: str, agent_prefix: str = "acmi") -> int:
    """Import ACMI file to TensorBoard format.

    Converts ACMI file to FlightEpisode and writes to TensorBoard logs.

    Args:
        acmi_file: Path to .txt.acmi file
        output_dir: TensorBoard log directory
        agent_prefix: Prefix for agent IDs (default: "acmi")

    Returns:
        Number of episodes imported

    Example:
        >>> count = import_acmi("mission.txt.acmi", "runs/imported")
        >>> print(f"Imported {count} episodes")
    """
    # Convert ACMI to episodes
    converter = ACMIConverter()
    episodes = converter.acmi_to_episodes(acmi_file)

    # Write to TensorBoard
    logger = FlightLogger(log_dir=output_dir)

    for episode in episodes:
        # Optionally prefix agent ID
        if agent_prefix and not episode.agent_id.startswith(agent_prefix):
            episode.agent_id = f"{agent_prefix}_{episode.agent_id}"

        logger.log_episode(episode)

    logger.close()

    print(f"Imported {len(episodes)} episodes from {acmi_file}")
    print(f"TensorBoard logs: {output_dir}")

    return len(episodes)


def export_to_acmi(
    logdir: str,
    output_file: str,
    episode_id: Optional[str] = None,
    agent_id: Optional[str] = None
) -> bool:
    """Export TensorBoard episode to ACMI file.

    Args:
        logdir: TensorBoard log directory
        output_file: Output .txt.acmi file path
        episode_id: Specific episode ID to export (optional)
        agent_id: Filter by agent ID (optional)

    Returns:
        True if export succeeded

    Example:
        >>> export_to_acmi("runs/training", "best_flight.txt.acmi",
        ...                episode_id="episode_142")
    """
    # This requires reading from TensorBoard event files
    # For now, we'll provide a placeholder that users can extend

    print(f"Export from {logdir} to {output_file}")
    print("Note: This requires plugin integration to read TensorBoard events")
    print("Use ACMIConverter.episode_to_acmi() with a FlightEpisode instance")

    return False


def batch_import_acmi(acmi_dir: str, output_dir: str, pattern: str = "*.txt.acmi") -> int:
    """Import all ACMI files from a directory.

    Args:
        acmi_dir: Directory containing ACMI files
        output_dir: TensorBoard log directory
        pattern: File pattern (default: "*.txt.acmi")

    Returns:
        Total number of episodes imported

    Example:
        >>> count = batch_import_acmi("acmi_files/", "runs/imported")
        >>> print(f"Imported {count} total episodes")
    """
    acmi_dir = Path(acmi_dir)
    total_episodes = 0

    for acmi_file in acmi_dir.glob(pattern):
        print(f"\nProcessing: {acmi_file.name}")
        count = import_acmi(str(acmi_file), output_dir)
        total_episodes += count

    print(f"\nTotal: {total_episodes} episodes imported")
    return total_episodes
