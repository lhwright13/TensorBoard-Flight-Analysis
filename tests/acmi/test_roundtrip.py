"""Tests for ACMI roundtrip conversion (lossless CAM)."""

import unittest
import tempfile
from pathlib import Path

from tensorboard_flight.data.schema import (
    FlightEpisode,
    FlightDataPoint,
    Orientation,
    Telemetry,
    RLMetrics,
)
from tensorboard_flight.acmi.converter import ACMIConverter


class TestACMIRoundtrip(unittest.TestCase):
    """Test lossless roundtrip conversion with CAM metadata."""

    def setUp(self):
        """Create temp directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def create_sample_episode(self):
        """Create a sample FlightEpisode with full CAM metadata."""
        trajectory = []

        for i in range(5):
            t = i * 0.1

            datapoint = FlightDataPoint(
                step=i,
                timestamp=t,
                position=(i * 10.0, i * 10.0, 1000.0 + i * 10.0),
                orientation=Orientation(roll=i * 1.0, pitch=5.0, yaw=90.0 + i),
                velocity=(25.0, 0.0, 2.0),
                angular_velocity=(0.01, 0.02, 0.03),
                telemetry=Telemetry(
                    airspeed=50.0 + i,
                    altitude=1000.0 + i * 10.0,
                    g_force=1.0 + i * 0.1,
                    throttle=0.7,
                    aoa=5.0,
                    aos=0.5,
                    heading=90.0 + i,
                    vertical_speed=2.0,
                    turn_rate=5.0,
                    bank_angle=i * 1.0,
                    aileron=0.1,
                    elevator=-0.05,
                    rudder=0.02,
                ),
                rl_metrics=RLMetrics(
                    reward=1.0 + i * 0.1,
                    cumulative_reward=i * 1.1,
                    action=[0.1, -0.05, 0.02, 0.7],
                    value_estimate=100.0 + i * 10.0,
                    policy_logprob=-1.2,
                    advantage=0.5,
                    entropy=0.8,
                    reward_components={
                        'tracking': 0.6 + i * 0.05,
                        'stability': 0.3,
                        'efficiency': 0.1,
                    },
                ),
            )
            trajectory.append(datapoint)

        episode = FlightEpisode(
            episode_id="test_episode_42",
            agent_id="test_agent",
            episode_number=42,
            start_time=0.0,
            trajectory=trajectory,
            total_steps=len(trajectory),
            total_reward=5.5,
            duration=0.4,
            success=True,
            termination_reason="completed",
            config={'policy': 'PPO', 'learning_rate': 0.0003},
            tags=['test', 'roundtrip'],
        )

        return episode

    def test_roundtrip_basic(self):
        """Test basic roundtrip conversion."""
        # Create episode
        episode1 = self.create_sample_episode()

        # Export to ACMI
        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        # Import back
        episodes = converter.acmi_to_episodes(str(acmi_file))
        self.assertEqual(len(episodes), 1)
        episode2 = episodes[0]

        # Verify basic properties
        self.assertEqual(episode2.agent_id, episode1.agent_id)
        self.assertEqual(len(episode2.trajectory), len(episode1.trajectory))

    def test_roundtrip_trajectory_data(self):
        """Test trajectory data preservation."""
        episode1 = self.create_sample_episode()

        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        episodes = converter.acmi_to_episodes(str(acmi_file))
        episode2 = episodes[0]

        # Check first datapoint
        dp1 = episode1.trajectory[0]
        dp2 = episode2.trajectory[0]

        # Position (with some tolerance for geodetic conversion)
        self.assertAlmostEqual(dp2.position[2], dp1.position[2], delta=1.0)

        # Orientation
        self.assertAlmostEqual(dp2.orientation.roll, dp1.orientation.roll, delta=0.1)
        self.assertAlmostEqual(dp2.orientation.pitch, dp1.orientation.pitch, delta=0.1)
        self.assertAlmostEqual(dp2.orientation.yaw, dp1.orientation.yaw, delta=0.1)

        # Telemetry
        self.assertAlmostEqual(dp2.telemetry.airspeed, dp1.telemetry.airspeed, delta=0.5)
        self.assertAlmostEqual(dp2.telemetry.altitude, dp1.telemetry.altitude, delta=1.0)
        self.assertAlmostEqual(dp2.telemetry.throttle, dp1.telemetry.throttle, delta=0.01)

    def test_roundtrip_rl_metrics(self):
        """Test RL metrics preservation (CAM)."""
        episode1 = self.create_sample_episode()

        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        episodes = converter.acmi_to_episodes(str(acmi_file))
        episode2 = episodes[0]

        dp1 = episode1.trajectory[2]  # Check middle datapoint
        dp2 = episode2.trajectory[2]

        # RL metrics
        self.assertAlmostEqual(dp2.rl_metrics.reward, dp1.rl_metrics.reward, delta=0.01)
        self.assertAlmostEqual(dp2.rl_metrics.cumulative_reward, dp1.rl_metrics.cumulative_reward, delta=0.01)

        # Action
        self.assertEqual(len(dp2.rl_metrics.action), len(dp1.rl_metrics.action))
        for i in range(len(dp1.rl_metrics.action)):
            self.assertAlmostEqual(dp2.rl_metrics.action[i], dp1.rl_metrics.action[i], delta=0.001)

        # Optional metrics
        if dp1.rl_metrics.value_estimate is not None:
            self.assertAlmostEqual(dp2.rl_metrics.value_estimate, dp1.rl_metrics.value_estimate, delta=0.1)

    def test_roundtrip_reward_components(self):
        """Test reward components preservation."""
        episode1 = self.create_sample_episode()

        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        episodes = converter.acmi_to_episodes(str(acmi_file))
        episode2 = episodes[0]

        dp1 = episode1.trajectory[0]
        dp2 = episode2.trajectory[0]

        if dp1.rl_metrics.reward_components:
            self.assertIsNotNone(dp2.rl_metrics.reward_components)
            # Note: component names are case-normalized
            for key, value in dp1.rl_metrics.reward_components.items():
                # Check if key exists (may be capitalized)
                found = False
                for key2, value2 in dp2.rl_metrics.reward_components.items():
                    if key.lower() == key2.lower():
                        self.assertAlmostEqual(value2, value, delta=0.01)
                        found = True
                        break
                self.assertTrue(found, f"Component {key} not found")

    def test_roundtrip_control_surfaces(self):
        """Test control surface preservation."""
        episode1 = self.create_sample_episode()

        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        episodes = converter.acmi_to_episodes(str(acmi_file))
        episode2 = episodes[0]

        dp1 = episode1.trajectory[0]
        dp2 = episode2.trajectory[0]

        if dp1.telemetry.aileron is not None:
            self.assertIsNotNone(dp2.telemetry.aileron)
            self.assertAlmostEqual(dp2.telemetry.aileron, dp1.telemetry.aileron, delta=0.01)

        if dp1.telemetry.elevator is not None:
            self.assertIsNotNone(dp2.telemetry.elevator)
            self.assertAlmostEqual(dp2.telemetry.elevator, dp1.telemetry.elevator, delta=0.01)

    def test_roundtrip_episode_metadata(self):
        """Test episode metadata preservation."""
        episode1 = self.create_sample_episode()

        acmi_file = self.temp_path / "test.txt.acmi"
        converter = ACMIConverter()
        converter.episode_to_acmi(episode1, str(acmi_file))

        episodes = converter.acmi_to_episodes(str(acmi_file))
        episode2 = episodes[0]

        # Episode metadata
        self.assertEqual(episode2.episode_id, episode1.episode_id)
        self.assertEqual(episode2.episode_number, episode1.episode_number)
        self.assertEqual(episode2.success, episode1.success)
        self.assertEqual(episode2.termination_reason, episode1.termination_reason)

        # Tags
        if episode1.tags:
            self.assertIsNotNone(episode2.tags)
            self.assertEqual(set(episode2.tags), set(episode1.tags))


if __name__ == '__main__':
    unittest.main()
