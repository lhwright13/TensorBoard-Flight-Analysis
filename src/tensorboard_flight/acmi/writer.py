"""ACMI file writer with CAM support.

This module writes FlightEpisode data to ACMI 2.2 text format with Custom Agent
Metadata (CAM) extensions for RL/AI data.
"""

from typing import TextIO, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .cam_schema import CAMEncoder, CAMKeys
from .geo_utils import cartesian_to_geodetic, compute_airspeed_from_velocity


class ACMIWriter:
    """Write FlightEpisode to ACMI 2.2 text format with CAM metadata.

    Example:
        >>> from tensorboard_flight import FlightEpisode
        >>> writer = ACMIWriter(reference_point=(34.9, -117.9, 700))
        >>> writer.write_episode(episode, "output.txt.acmi")
    """

    def __init__(
        self,
        reference_point: Optional[Tuple[float, float, float]] = None,
        compress: bool = False
    ):
        """Initialize ACMI writer.

        Args:
            reference_point: (lat, lon, alt) origin for coordinate conversion.
                           If None, will be set to default Edwards AFB.
            compress: If True, compress output with gzip (future feature)
        """
        self.reference_point = reference_point
        self.compress = compress
        self.encoder = CAMEncoder()

    def write_episode(self, episode, output_path: str):
        """Write complete episode to ACMI file.

        Args:
            episode: FlightEpisode instance to export
            output_path: Output .txt.acmi file path
        """
        output_path = Path(output_path)

        # Ensure .txt.acmi extension
        if not str(output_path).endswith('.txt.acmi'):
            output_path = output_path.with_suffix('.txt.acmi')

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_header(f, episode)
            self._write_trajectory(f, episode)
            self._write_footer(f, episode)

    def _write_header(self, f: TextIO, episode):
        """Write ACMI file header and global metadata.

        Args:
            f: File object
            episode: FlightEpisode instance
        """
        # Required header
        f.write("FileType=text/acmi/tacview\n")
        f.write("FileVersion=2.2\n")
        f.write("\n")

        # Global metadata (object ID 0)
        ref_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        f.write(f"0,ReferenceTime={ref_time}\n")
        f.write(f'0,Title="{episode.episode_id}"\n')
        f.write('0,Author="TensorBoard Flight Plugin"\n')
        f.write(f'0,Comments="RL Episode {episode.episode_number} - {episode.agent_id}"\n')

        # Optional: add episode-level CAM metadata as global props
        if episode.config and 'policy' in episode.config:
            f.write(f'0,{CAMKeys.POLICY}="{episode.config["policy"]}"\n')

        f.write("\n")

    def _write_trajectory(self, f: TextIO, episode):
        """Write trajectory data with CAM metadata.

        Args:
            f: File object
            episode: FlightEpisode instance
        """
        # Use agent_id as object ID (convert to hex)
        obj_id = self._agent_id_to_hex(episode.agent_id)

        # Determine if we have orientation data
        has_orientation = (
            episode.trajectory and
            episode.trajectory[0].orientation is not None
        )

        # First record: Create object with metadata
        f.write("#0.0\n")
        props = [
            "Type=Air+FixedWing",
            f'Name="{episode.agent_id}"',
            'Pilot="RL_Agent"',
            'Coalition=Blue',
            'Color=Blue',
        ]

        # Add episode metadata (CAM)
        episode_meta = self.encoder.encode_episode_metadata(episode)
        props.extend(self._format_properties(episode_meta))

        f.write(f"{obj_id},{','.join(props)}\n")
        f.write("\n")

        # Write each datapoint
        last_idx = len(episode.trajectory) - 1
        for i, datapoint in enumerate(episode.trajectory):
            self._write_datapoint(f, obj_id, datapoint, is_last=(i == last_idx))

            # Add newline every 10 frames for readability
            if i % 10 == 9:
                f.write("\n")

    def _write_datapoint(self, f: TextIO, obj_id: str, dp, is_last: bool):
        """Write single timestep with full CAM metadata.

        Args:
            f: File object
            obj_id: Object ID hex string
            dp: FlightDataPoint instance
            is_last: Whether this is the last datapoint
        """
        # Time frame
        f.write(f"#{dp.timestamp:.3f}\n")

        # Convert position to geodetic
        lat, lon, alt = cartesian_to_geodetic(dp.position, self.reference_point)

        # Build property list
        props = []

        # Transform (position + orientation)
        if dp.orientation is not None:
            transform = (
                f"{lon:.7f}|{lat:.7f}|{alt:.2f}|"
                f"{dp.orientation.roll:.2f}|{dp.orientation.pitch:.2f}|{dp.orientation.yaw:.2f}"
            )
        else:
            # Position only
            transform = f"{lon:.7f}|{lat:.7f}|{alt:.2f}"

        props.append(f"T={transform}")

        # Standard ACMI telemetry
        props.append(f"IAS={dp.telemetry.airspeed:.2f}")
        props.append(f"Throttle={dp.telemetry.throttle:.3f}")

        if abs(dp.telemetry.aoa) > 0.01:
            props.append(f"AOA={dp.telemetry.aoa:.2f}")
        if abs(dp.telemetry.aos) > 0.01:
            props.append(f"AOS={dp.telemetry.aos:.2f}")
        if dp.orientation:
            props.append(f"Heading={dp.telemetry.heading:.2f}")

        # CAM: G-force
        g_props = self.encoder.encode_g_force(dp.telemetry.g_force)
        props.extend(self._format_properties(g_props))

        # CAM: Angular velocity (body rates)
        if dp.angular_velocity is not None:
            angular_props = self.encoder.encode_angular_velocity(dp.angular_velocity)
            props.extend(self._format_properties(angular_props))

        # CAM: Control surfaces
        control_props = self.encoder.encode_control_surfaces(dp.telemetry)
        props.extend(self._format_properties(control_props))

        # CAM: RL metrics
        if dp.rl_metrics:
            rl_props = self.encoder.encode_rl_metrics(dp.rl_metrics)
            props.extend(self._format_properties(rl_props))

        f.write(f"{obj_id},{','.join(props)}\n")

    def _write_footer(self, f: TextIO, episode):
        """Write final metadata and remove object.

        Args:
            f: File object
            episode: FlightEpisode instance
        """
        if not episode.trajectory:
            return

        # Last timeframe with termination data
        last_time = episode.trajectory[-1].timestamp
        obj_id = self._agent_id_to_hex(episode.agent_id)

        f.write(f"\n#{last_time + 0.001:.3f}\n")
        term_props = self.encoder.encode_episode_termination(episode)
        props = self._format_properties(term_props)
        f.write(f"{obj_id},{','.join(props)}\n")

        # Remove object
        f.write(f"\n#{last_time + 0.1:.3f}\n")
        f.write(f"-{obj_id}\n")

    def _format_properties(self, props: dict) -> list:
        """Format properties dict as key=value strings.

        Args:
            props: Dictionary of properties

        Returns:
            List of "key=value" strings
        """
        formatted = []
        for key, value in props.items():
            if isinstance(value, str):
                # Quote strings that aren't already quoted
                if not (value.startswith('"') and value.endswith('"')):
                    value = f'"{value}"'
                formatted.append(f'{key}={value}')
            elif isinstance(value, bool):
                # Boolean as lowercase
                formatted.append(f'{key}={str(value).lower()}')
            elif isinstance(value, (int, float)):
                # Numbers
                if isinstance(value, float):
                    formatted.append(f'{key}={value:.6f}')
                else:
                    formatted.append(f'{key}={value}')
            elif value is None:
                formatted.append(f'{key}=null')
            else:
                formatted.append(f'{key}={value}')

        return formatted

    def _agent_id_to_hex(self, agent_id: str) -> str:
        """Convert agent_id to hex object ID.

        Uses hash to generate consistent hex ID from agent name.

        Args:
            agent_id: Agent identifier string

        Returns:
            Hex string (8 characters)
        """
        # Simple hash to hex (32-bit)
        hash_val = hash(agent_id) & 0xFFFFFFFF
        return f"{hash_val:08x}"


def write_multiple_episodes(episodes: list, output_dir: str, prefix: str = "episode"):
    """Write multiple episodes to separate ACMI files.

    Args:
        episodes: List of FlightEpisode instances
        output_dir: Output directory path
        prefix: Filename prefix (default: "episode")

    Example:
        >>> episodes = [episode1, episode2, episode3]
        >>> write_multiple_episodes(episodes, "output/acmi", prefix="training")
        # Creates: training_0000.txt.acmi, training_0001.txt.acmi, ...
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    writer = ACMIWriter()

    for i, episode in enumerate(episodes):
        filename = f"{prefix}_{i:04d}.txt.acmi"
        output_path = output_dir / filename

        writer.write_episode(episode, str(output_path))

        print(f"Wrote {filename}: {len(episode.trajectory)} timesteps")
