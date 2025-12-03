"""Unit tests for FlightLogger."""

import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import json

from tensorboard_flight import FlightLogger
from tensorboard_flight.data.schema import FlightEpisode


class TestFlightLogger:
    """Test FlightLogger class."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_create_logger(self, temp_log_dir):
        """Test creating logger."""
        logger = FlightLogger(log_dir=temp_log_dir)
        assert logger.log_dir == Path(temp_log_dir)
        assert logger.episode_number == 0
        assert logger.current_episode is None
        logger.close()

    def test_start_episode(self, temp_log_dir):
        """Test starting episode."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        assert logger.current_episode is not None
        assert logger.current_agent_id == "test_agent"
        assert logger.cumulative_reward == 0.0
        assert len(logger.current_episode) == 0

        logger.close()

    def test_log_flight_data(self, temp_log_dir):
        """Test logging flight data."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        logger.log_flight_data(
            step=0,
            agent_id="test_agent",
            position=(0.0, 0.0, 100.0),
            orientation=(0.0, 0.0, 0.0),
            velocity=(25.0, 0.0, 0.0),
            telemetry={
                'airspeed': 25.0,
                'altitude': 100.0,
                'g_force': 1.0,
                'throttle': 0.8,
                'aoa': 5.0,
                'aos': 0.0,
                'heading': 0.0,
                'vertical_speed': 0.0,
                'turn_rate': 0.0,
                'bank_angle': 0.0,
            },
            rl_metrics={
                'reward': 1.0,
                'action': [0.1, 0.2, 0.3, 0.8],
            },
        )

        assert len(logger.current_episode) == 1
        assert logger.cumulative_reward == 1.0

        logger.close()

    def test_log_multiple_steps(self, temp_log_dir):
        """Test logging multiple steps."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        for step in range(10):
            logger.log_flight_data(
                step=step,
                agent_id="test_agent",
                position=(0.0, 0.0, 100.0 + step),
                orientation=(0.0, 0.0, 0.0),
                velocity=(25.0, 0.0, 0.0),
                telemetry={
                    'airspeed': 25.0,
                    'altitude': 100.0 + step,
                    'g_force': 1.0,
                    'throttle': 0.8,
                    'aoa': 5.0,
                    'aos': 0.0,
                    'heading': 0.0,
                    'vertical_speed': 0.0,
                    'turn_rate': 0.0,
                    'bank_angle': 0.0,
                },
                rl_metrics={
                    'reward': 1.0,
                    'action': [0.1, 0.2, 0.3, 0.8],
                },
            )

        assert len(logger.current_episode) == 10
        assert logger.cumulative_reward == 10.0

        logger.close()

    def test_end_episode(self, temp_log_dir):
        """Test ending episode."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        logger.log_flight_data(
            step=0,
            agent_id="test_agent",
            position=(0.0, 0.0, 100.0),
            orientation=(0.0, 0.0, 0.0),
            velocity=(25.0, 0.0, 0.0),
            telemetry={
                'airspeed': 25.0,
                'altitude': 100.0,
                'g_force': 1.0,
                'throttle': 0.8,
                'aoa': 5.0,
                'aos': 0.0,
                'heading': 0.0,
                'vertical_speed': 0.0,
                'turn_rate': 0.0,
                'bank_angle': 0.0,
            },
            rl_metrics={
                'reward': 1.0,
                'action': [0.1, 0.2, 0.3, 0.8],
            },
        )

        logger.end_episode(success=True, termination_reason="completed")

        assert logger.current_episode is None
        assert logger.episode_number == 1

        logger.close()

    def test_multiple_episodes(self, temp_log_dir):
        """Test logging multiple episodes."""
        logger = FlightLogger(log_dir=temp_log_dir)

        for episode in range(3):
            logger.start_episode(agent_id="test_agent")

            for step in range(5):
                logger.log_flight_data(
                    step=step,
                    agent_id="test_agent",
                    position=(0.0, 0.0, 100.0),
                    orientation=(0.0, 0.0, 0.0),
                    velocity=(25.0, 0.0, 0.0),
                    telemetry={
                        'airspeed': 25.0,
                        'altitude': 100.0,
                        'g_force': 1.0,
                        'throttle': 0.8,
                        'aoa': 5.0,
                        'aos': 0.0,
                        'heading': 0.0,
                        'vertical_speed': 0.0,
                        'turn_rate': 0.0,
                        'bank_angle': 0.0,
                    },
                    rl_metrics={
                        'reward': 1.0,
                        'action': [0.1, 0.2, 0.3, 0.8],
                    },
                )

            logger.end_episode(success=True, termination_reason="completed")

        assert logger.episode_number == 3

        logger.close()

    def test_auto_start_episode(self, temp_log_dir):
        """Test auto-starting episode."""
        logger = FlightLogger(log_dir=temp_log_dir)

        # Log without explicitly starting episode
        logger.log_flight_data(
            step=0,
            agent_id="test_agent",
            position=(0.0, 0.0, 100.0),
            orientation=(0.0, 0.0, 0.0),
            velocity=(25.0, 0.0, 0.0),
            telemetry={
                'airspeed': 25.0,
                'altitude': 100.0,
                'g_force': 1.0,
                'throttle': 0.8,
                'aoa': 5.0,
                'aos': 0.0,
                'heading': 0.0,
                'vertical_speed': 0.0,
                'turn_rate': 0.0,
                'bank_angle': 0.0,
            },
            rl_metrics={
                'reward': 1.0,
                'action': [0.1, 0.2, 0.3, 0.8],
            },
        )

        assert logger.current_episode is not None
        assert logger.current_agent_id == "test_agent"

        logger.close()

    def test_numpy_types(self, temp_log_dir):
        """Test with numpy types."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        logger.log_flight_data(
            step=np.int32(0),
            agent_id="test_agent",
            position=(np.float32(0.0), np.float32(0.0), np.float32(100.0)),
            orientation=(np.float32(0.0), np.float32(0.0), np.float32(0.0)),
            velocity=np.array([25.0, 0.0, 0.0], dtype=np.float32),
            telemetry={
                'airspeed': np.float32(25.0),
                'altitude': np.float32(100.0),
                'g_force': np.float32(1.0),
                'throttle': np.float32(0.8),
                'aoa': np.float32(5.0),
                'aos': np.float32(0.0),
                'heading': np.float32(0.0),
                'vertical_speed': np.float32(0.0),
                'turn_rate': np.float32(0.0),
                'bank_angle': np.float32(0.0),
            },
            rl_metrics={
                'reward': np.float32(1.0),
                'action': np.array([0.1, 0.2, 0.3, 0.8], dtype=np.float32),
            },
        )

        logger.end_episode(success=True, termination_reason="completed")

        # Should not raise any JSON serialization errors
        logger.close()

    def test_event_logging(self, temp_log_dir):
        """Test logging events."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        logger.log_flight_data(
            step=0,
            agent_id="test_agent",
            position=(0.0, 0.0, 100.0),
            orientation=(0.0, 0.0, 0.0),
            velocity=(25.0, 0.0, 0.0),
            telemetry={
                'airspeed': 25.0,
                'altitude': 100.0,
                'g_force': 1.0,
                'throttle': 0.8,
                'aoa': 5.0,
                'aos': 0.0,
                'heading': 0.0,
                'vertical_speed': 0.0,
                'turn_rate': 0.0,
                'bank_angle': 0.0,
            },
            rl_metrics={
                'reward': 1.0,
                'action': [0.1, 0.2, 0.3, 0.8],
            },
            events=[
                {
                    'timestamp': 0.0,
                    'type': 'checkpoint',
                    'severity': 'info',
                    'message': 'Checkpoint reached',
                }
            ],
        )

        assert len(logger.current_episode) == 1
        assert logger.current_episode[0].events is not None
        assert len(logger.current_episode[0].events) == 1

        logger.close()

    def test_log_dir_creation(self):
        """Test log directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "nested" / "log" / "dir"
            logger = FlightLogger(log_dir=str(log_dir))

            assert log_dir.exists()
            assert log_dir.is_dir()

            logger.close()

    def test_event_file_created(self, temp_log_dir):
        """Test that event files are created."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="test_agent")

        logger.log_flight_data(
            step=0,
            agent_id="test_agent",
            position=(0.0, 0.0, 100.0),
            orientation=(0.0, 0.0, 0.0),
            velocity=(25.0, 0.0, 0.0),
            telemetry={
                'airspeed': 25.0,
                'altitude': 100.0,
                'g_force': 1.0,
                'throttle': 0.8,
                'aoa': 5.0,
                'aos': 0.0,
                'heading': 0.0,
                'vertical_speed': 0.0,
                'turn_rate': 0.0,
                'bank_angle': 0.0,
            },
            rl_metrics={
                'reward': 1.0,
                'action': [0.1, 0.2, 0.3, 0.8],
            },
        )

        logger.end_episode(success=True, termination_reason="completed")
        logger.close()

        # Check that event files exist
        event_files = list(Path(temp_log_dir).glob("events.out.tfevents.*"))
        assert len(event_files) > 0

    def test_agent_id_mismatch(self, temp_log_dir):
        """Test error on agent ID mismatch."""
        logger = FlightLogger(log_dir=temp_log_dir)
        logger.start_episode(agent_id="agent1")

        with pytest.raises(ValueError, match="Agent ID mismatch"):
            logger.log_flight_data(
                step=0,
                agent_id="agent2",  # Different agent ID
                position=(0.0, 0.0, 100.0),
                orientation=(0.0, 0.0, 0.0),
                velocity=(25.0, 0.0, 0.0),
                telemetry={
                    'airspeed': 25.0,
                    'altitude': 100.0,
                    'g_force': 1.0,
                    'throttle': 0.8,
                    'aoa': 5.0,
                    'aos': 0.0,
                    'heading': 0.0,
                    'vertical_speed': 0.0,
                    'turn_rate': 0.0,
                    'bank_angle': 0.0,
                },
                rl_metrics={
                    'reward': 1.0,
                    'action': [0.1, 0.2, 0.3, 0.8],
                },
            )

        logger.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
