"""Unit tests for data schema."""

import pytest
import numpy as np
from tensorboard_flight.data.schema import (
    Orientation,
    Telemetry,
    RLMetrics,
    Event,
    FlightDataPoint,
    FlightEpisode,
    _to_python_type,
)


class TestTypesConversion:
    """Test numpy type conversion."""

    def test_numpy_float_conversion(self):
        """Test numpy float types convert to Python float."""
        assert isinstance(_to_python_type(np.float32(1.5)), float)
        assert isinstance(_to_python_type(np.float64(2.5)), float)
        assert _to_python_type(np.float32(1.5)) == 1.5

    def test_numpy_int_conversion(self):
        """Test numpy int types convert to Python int."""
        assert isinstance(_to_python_type(np.int32(42)), int)
        assert isinstance(_to_python_type(np.int64(100)), int)
        assert _to_python_type(np.int32(42)) == 42

    def test_numpy_array_conversion(self):
        """Test numpy arrays convert to lists."""
        arr = np.array([1.0, 2.0, 3.0])
        result = _to_python_type(arr)
        assert isinstance(result, list)
        assert result == [1.0, 2.0, 3.0]

    def test_dict_conversion(self):
        """Test dict with numpy values."""
        data = {
            'a': np.float32(1.5),
            'b': np.int32(42),
            'c': np.array([1, 2, 3]),
        }
        result = _to_python_type(data)
        assert isinstance(result['a'], float)
        assert isinstance(result['b'], int)
        assert isinstance(result['c'], list)

    def test_nested_conversion(self):
        """Test nested structures."""
        data = {
            'nested': {
                'value': np.float32(1.5),
                'array': np.array([1.0, 2.0]),
            },
            'list': [np.int32(1), np.int32(2)],
        }
        result = _to_python_type(data)
        assert isinstance(result['nested']['value'], float)
        assert isinstance(result['nested']['array'], list)
        assert all(isinstance(x, int) for x in result['list'])


class TestOrientation:
    """Test Orientation class."""

    def test_create_orientation(self):
        """Test creating orientation."""
        ori = Orientation(roll=10.0, pitch=5.0, yaw=180.0)
        assert ori.roll == 10.0
        assert ori.pitch == 5.0
        assert ori.yaw == 180.0

    def test_orientation_to_dict(self):
        """Test orientation serialization."""
        ori = Orientation(
            roll=np.float32(10.0),
            pitch=np.float32(5.0),
            yaw=np.float32(180.0)
        )
        result = ori.to_dict()
        assert isinstance(result['roll'], float)
        assert isinstance(result['pitch'], float)
        assert isinstance(result['yaw'], float)
        assert result['roll'] == 10.0


class TestTelemetry:
    """Test Telemetry class."""

    def test_create_telemetry(self):
        """Test creating telemetry."""
        tel = Telemetry(
            airspeed=25.0,
            altitude=100.0,
            g_force=1.2,
            throttle=0.8,
            aoa=5.0,
            aos=0.5,
            heading=90.0,
            vertical_speed=2.0,
            turn_rate=10.0,
            bank_angle=15.0,
        )
        assert tel.airspeed == 25.0
        assert tel.altitude == 100.0

    def test_telemetry_with_controls(self):
        """Test telemetry with control surfaces."""
        tel = Telemetry(
            airspeed=25.0,
            altitude=100.0,
            g_force=1.0,
            throttle=0.8,
            aoa=5.0,
            aos=0.0,
            heading=90.0,
            vertical_speed=2.0,
            turn_rate=10.0,
            bank_angle=15.0,
            aileron=0.5,
            elevator=-0.2,
            rudder=0.1,
        )
        assert tel.aileron == 0.5
        assert tel.elevator == -0.2
        assert tel.rudder == 0.1

    def test_telemetry_to_dict(self):
        """Test telemetry serialization."""
        tel = Telemetry(
            airspeed=np.float32(25.0),
            altitude=np.float32(100.0),
            g_force=np.float32(1.2),
            throttle=np.float32(0.8),
            aoa=np.float32(5.0),
            aos=np.float32(0.5),
            heading=np.float32(90.0),
            vertical_speed=np.float32(2.0),
            turn_rate=np.float32(10.0),
            bank_angle=np.float32(15.0),
        )
        result = tel.to_dict()
        assert all(isinstance(v, float) for v in result.values())


class TestRLMetrics:
    """Test RLMetrics class."""

    def test_create_rl_metrics(self):
        """Test creating RL metrics."""
        metrics = RLMetrics(
            reward=1.5,
            cumulative_reward=10.0,
            action=[0.1, 0.2, 0.3],
        )
        assert metrics.reward == 1.5
        assert metrics.cumulative_reward == 10.0
        assert metrics.action == [0.1, 0.2, 0.3]

    def test_rl_metrics_with_optionals(self):
        """Test RL metrics with optional fields."""
        metrics = RLMetrics(
            reward=1.5,
            cumulative_reward=10.0,
            action=[0.1, 0.2, 0.3],
            policy_logprob=-2.5,
            value_estimate=5.0,
            advantage=0.8,
            entropy=1.2,
        )
        assert metrics.policy_logprob == -2.5
        assert metrics.value_estimate == 5.0
        assert metrics.advantage == 0.8
        assert metrics.entropy == 1.2

    def test_rl_metrics_to_dict(self):
        """Test RL metrics serialization."""
        metrics = RLMetrics(
            reward=np.float32(1.5),
            cumulative_reward=np.float32(10.0),
            action=np.array([0.1, 0.2, 0.3]),
        )
        result = metrics.to_dict()
        assert isinstance(result['reward'], float)
        assert isinstance(result['cumulative_reward'], float)
        assert isinstance(result['action'], list)


class TestEvent:
    """Test Event class."""

    def test_create_event(self):
        """Test creating event."""
        event = Event(
            timestamp=1.5,
            event_type="crash",
            severity="error",
            message="Aircraft crashed",
        )
        assert event.timestamp == 1.5
        assert event.event_type == "crash"
        assert event.severity == "error"

    def test_event_with_metadata(self):
        """Test event with metadata."""
        event = Event(
            timestamp=1.5,
            event_type="checkpoint",
            severity="info",
            message="Checkpoint reached",
            metadata={"checkpoint_id": 3},
        )
        assert event.metadata == {"checkpoint_id": 3}

    def test_event_to_dict(self):
        """Test event serialization."""
        event = Event(
            timestamp=np.float32(1.5),
            event_type="crash",
            severity="error",
            message="Aircraft crashed",
        )
        result = event.to_dict()
        assert isinstance(result['timestamp'], float)


class TestFlightDataPoint:
    """Test FlightDataPoint class."""

    def test_create_flight_data_point(self):
        """Test creating flight data point."""
        point = FlightDataPoint(
            timestamp=1.5,
            step=10,
            position=np.array([0.0, 0.0, 100.0]),
            orientation=Orientation(roll=0.0, pitch=0.0, yaw=0.0),
            velocity=np.array([25.0, 0.0, 0.0]),
            angular_velocity=np.array([0.0, 0.0, 0.0]),
            telemetry=Telemetry(
                airspeed=25.0, altitude=100.0, g_force=1.0,
                throttle=0.8, aoa=5.0, aos=0.0, heading=0.0,
                vertical_speed=0.0, turn_rate=0.0, bank_angle=0.0,
            ),
            rl_metrics=RLMetrics(
                reward=1.0, cumulative_reward=10.0, action=[0.1, 0.2, 0.3],
            ),
        )
        assert point.step == 10
        assert len(point.position) == 3

    def test_flight_data_point_to_dict(self):
        """Test flight data point serialization."""
        point = FlightDataPoint(
            timestamp=np.float32(1.5),
            step=np.int32(10),
            position=np.array([0.0, 0.0, 100.0], dtype=np.float32),
            orientation=Orientation(roll=0.0, pitch=0.0, yaw=0.0),
            velocity=np.array([25.0, 0.0, 0.0], dtype=np.float32),
            angular_velocity=np.array([0.0, 0.0, 0.0], dtype=np.float32),
            telemetry=Telemetry(
                airspeed=25.0, altitude=100.0, g_force=1.0,
                throttle=0.8, aoa=5.0, aos=0.0, heading=0.0,
                vertical_speed=0.0, turn_rate=0.0, bank_angle=0.0,
            ),
            rl_metrics=RLMetrics(
                reward=1.0, cumulative_reward=10.0, action=[0.1, 0.2, 0.3],
            ),
        )
        result = point.to_dict()

        # Check types
        assert isinstance(result['timestamp'], float)
        assert isinstance(result['step'], int)
        assert isinstance(result['position'], list)
        assert isinstance(result['velocity'], list)
        assert isinstance(result['orientation'], dict)
        assert isinstance(result['telemetry'], dict)
        assert isinstance(result['rl_metrics'], dict)

        # Check values
        assert result['step'] == 10
        assert len(result['position']) == 3


class TestFlightEpisode:
    """Test FlightEpisode class."""

    def test_create_flight_episode(self):
        """Test creating flight episode."""
        episode = FlightEpisode(
            episode_id="test_ep_0",
            agent_id="test_agent",
            episode_number=0,
            start_time=1000.0,
            duration=10.0,
            total_steps=100,
            total_reward=50.0,
            success=True,
            termination_reason="completed",
        )
        assert episode.episode_id == "test_ep_0"
        assert episode.total_steps == 100
        assert episode.success is True

    def test_flight_episode_with_trajectory(self):
        """Test episode with trajectory."""
        point = FlightDataPoint(
            timestamp=1.5,
            step=10,
            position=np.array([0.0, 0.0, 100.0]),
            orientation=Orientation(roll=0.0, pitch=0.0, yaw=0.0),
            velocity=np.array([25.0, 0.0, 0.0]),
            angular_velocity=np.array([0.0, 0.0, 0.0]),
            telemetry=Telemetry(
                airspeed=25.0, altitude=100.0, g_force=1.0,
                throttle=0.8, aoa=5.0, aos=0.0, heading=0.0,
                vertical_speed=0.0, turn_rate=0.0, bank_angle=0.0,
            ),
            rl_metrics=RLMetrics(
                reward=1.0, cumulative_reward=10.0, action=[0.1, 0.2, 0.3],
            ),
        )

        episode = FlightEpisode(
            episode_id="test_ep_0",
            agent_id="test_agent",
            episode_number=0,
            start_time=1000.0,
            duration=10.0,
            total_steps=1,
            total_reward=1.0,
            success=True,
            termination_reason="completed",
            trajectory=[point],
        )
        assert len(episode.trajectory) == 1

    def test_flight_episode_to_dict(self):
        """Test episode serialization."""
        episode = FlightEpisode(
            episode_id="test_ep_0",
            agent_id="test_agent",
            episode_number=np.int32(0),
            start_time=np.float64(1000.0),
            duration=np.float32(10.0),
            total_steps=np.int32(100),
            total_reward=np.float32(50.0),
            success=True,
            termination_reason="completed",
        )
        result = episode.to_dict()

        # Check types
        assert isinstance(result['episode_number'], int)
        assert isinstance(result['start_time'], float)
        assert isinstance(result['duration'], float)
        assert isinstance(result['total_steps'], int)
        assert isinstance(result['total_reward'], float)
        assert isinstance(result['success'], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
