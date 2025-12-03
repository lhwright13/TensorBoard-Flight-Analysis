"""ACMI-enabled logger for RL training with automatic export.

This module provides ACMILogger, which extends FlightLogger with automatic
ACMI export capability for easy integration with RL frameworks.
"""

from typing import Optional
from pathlib import Path

from tensorboard_flight import FlightLogger
from .writer import ACMIWriter


class ACMILogger(FlightLogger):
    """Extended FlightLogger with automatic ACMI export.

    This logger writes to both TensorBoard format AND generates ACMI files
    automatically, making it easy to:
    - View training in TensorBoard Flight tab
    - Share flights as ACMI files with colleagues
    - View flights in Tacview for detailed analysis
    - Archive training data in standard format

    Example:
        >>> # Drop-in replacement for FlightLogger
        >>> logger = ACMILogger("runs/training", enable_acmi_export=True)
        >>> logger.start_episode("my_agent")
        >>> logger.log_flight_data(...)
        >>> logger.end_episode(success=True)
        >>> # Creates both TensorBoard logs AND episode_0000.txt.acmi

        >>> # Use with SB3 callback
        >>> from tensorboard_flight.callbacks import FlightLoggerCallback
        >>> logger = ACMILogger("runs/training", enable_acmi_export=True,
        ...                     acmi_dir="runs/training/acmi")
        >>> callback = FlightLoggerCallback(logger)
        >>> model.learn(callback=callback)
    """

    def __init__(
        self,
        log_dir: str,
        enable_acmi_export: bool = False,
        acmi_dir: Optional[str] = None,
        acmi_export_interval: int = 1,
        acmi_prefix: str = "episode",
        max_buffer_size: int = 100,
        flush_secs: float = 120,
        reference_point: Optional[tuple] = None,
    ):
        """Initialize ACMI-enabled flight logger.

        Args:
            log_dir: TensorBoard log directory
            enable_acmi_export: If True, automatically export episodes to ACMI
            acmi_dir: Directory for ACMI files (default: log_dir/acmi)
            acmi_export_interval: Export every N episodes (1 = all, 10 = every 10th)
            acmi_prefix: Filename prefix for ACMI files
            max_buffer_size: Max episodes to buffer before flushing
            flush_secs: Auto-flush interval in seconds
            reference_point: (lat, lon, alt) for ACMI coordinates
        """
        super().__init__(
            log_dir=log_dir,
            max_buffer_size=max_buffer_size,
            flush_secs=flush_secs,
        )

        self.enable_acmi_export = enable_acmi_export
        self.acmi_export_interval = acmi_export_interval
        self.acmi_prefix = acmi_prefix

        # Setup ACMI directory
        if acmi_dir is None:
            self.acmi_dir = Path(log_dir) / "acmi"
        else:
            self.acmi_dir = Path(acmi_dir)

        if self.enable_acmi_export:
            self.acmi_dir.mkdir(parents=True, exist_ok=True)

        # ACMI writer
        self.acmi_writer = ACMIWriter(reference_point=reference_point)

        # Episode counter for ACMI files
        self.acmi_episode_counter = 0

    def end_episode(
        self,
        success: bool = True,
        termination_reason: str = "completed",
        config: Optional[dict] = None,
        tags: Optional[list] = None,
    ):
        """End current episode and optionally export to ACMI.

        Args:
            success: Whether episode was successful
            termination_reason: Reason for termination
            config: Episode configuration dict
            tags: List of tags for this episode
        """
        # Call parent to log to TensorBoard
        super().end_episode(
            success=success,
            termination_reason=termination_reason,
            config=config,
            tags=tags,
        )

        # Export to ACMI if enabled and interval matches
        if self.enable_acmi_export:
            if self.acmi_episode_counter % self.acmi_export_interval == 0:
                self._export_current_episode_to_acmi()

            self.acmi_episode_counter += 1

    def _export_current_episode_to_acmi(self):
        """Export the most recently completed episode to ACMI file."""
        if not self.current_episode:
            return

        # Generate filename
        filename = f"{self.acmi_prefix}_{self.acmi_episode_counter:04d}.txt.acmi"
        output_path = self.acmi_dir / filename

        try:
            # Write to ACMI
            self.acmi_writer.write_episode(self.current_episode, str(output_path))

            if self.verbose:
                print(f"Exported ACMI: {filename}")

        except Exception as e:
            print(f"Warning: Failed to export ACMI {filename}: {e}")

    def export_episode_to_acmi(self, episode, output_file: str):
        """Manually export a specific episode to ACMI.

        Args:
            episode: FlightEpisode instance
            output_file: Output .txt.acmi file path

        Example:
            >>> logger.export_episode_to_acmi(best_episode, "best_flight.txt.acmi")
        """
        self.acmi_writer.write_episode(episode, output_file)

    def set_acmi_reference_point(self, lat: float, lon: float, alt: float):
        """Update the reference point for ACMI coordinate conversion.

        Args:
            lat: Reference latitude in degrees
            lon: Reference longitude in degrees
            alt: Reference altitude in meters MSL

        Example:
            >>> # Set reference to Edwards AFB
            >>> logger.set_acmi_reference_point(34.9054, -117.8839, 700.0)
        """
        self.acmi_writer.reference_point = (lat, lon, alt)

    def get_acmi_files(self) -> list:
        """Get list of ACMI files created by this logger.

        Returns:
            List of Path objects for .txt.acmi files

        Example:
            >>> files = logger.get_acmi_files()
            >>> print(f"Created {len(files)} ACMI files")
        """
        if not self.acmi_dir.exists():
            return []

        return sorted(self.acmi_dir.glob(f"{self.acmi_prefix}_*.txt.acmi"))
