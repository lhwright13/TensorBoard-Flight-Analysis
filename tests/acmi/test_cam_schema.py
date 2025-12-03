"""Tests for CAM schema encoding/decoding."""

import unittest
from tensorboard_flight.acmi.cam_schema import CAMEncoder, CAMDecoder, CAMKeys
from tensorboard_flight.data.schema import RLMetrics, Telemetry


class TestCAMEncoder(unittest.TestCase):
    """Test CAM encoding."""

    def test_encode_rl_metrics_basic(self):
        """Test encoding basic RL metrics."""
        metrics = RLMetrics(
            reward=1.5,
            cumulative_reward=10.5,
            action=[0.1, 0.2, 0.3, 0.7],
        )

        props = CAMEncoder.encode_rl_metrics(metrics)

        self.assertEqual(props[CAMKeys.REWARD_INSTANT], 1.5)
        self.assertEqual(props[CAMKeys.REWARD_CUM], 10.5)
        self.assertEqual(props['Agent.Action.0'], 0.1)
        self.assertEqual(props['Agent.Action.1'], 0.2)
        self.assertEqual(props['Agent.Action.2'], 0.3)
        self.assertEqual(props['Agent.Action.3'], 0.7)

    def test_encode_rl_metrics_optional(self):
        """Test encoding optional RL metrics."""
        metrics = RLMetrics(
            reward=1.0,
            cumulative_reward=5.0,
            action=[0.0],
            value_estimate=100.5,
            policy_logprob=-1.2,
            advantage=0.5,
            entropy=0.8,
        )

        props = CAMEncoder.encode_rl_metrics(metrics)

        self.assertEqual(props[CAMKeys.VALUE], 100.5)
        self.assertEqual(props[CAMKeys.LOG_PROB], -1.2)
        self.assertEqual(props[CAMKeys.ADVANTAGE], 0.5)
        self.assertEqual(props[CAMKeys.ENTROPY], 0.8)

    def test_encode_reward_components(self):
        """Test encoding reward components."""
        metrics = RLMetrics(
            reward=1.0,
            cumulative_reward=1.0,
            action=[0.0],
            reward_components={'tracking': 0.8, 'stability': 0.2},
        )

        props = CAMEncoder.encode_rl_metrics(metrics)

        self.assertEqual(props['Agent.Reward.Tracking'], 0.8)
        self.assertEqual(props['Agent.Reward.Stability'], 0.2)

    def test_encode_control_surfaces(self):
        """Test encoding control surfaces."""
        telemetry = Telemetry(
            airspeed=50.0,
            altitude=1000.0,
            g_force=1.2,
            throttle=0.7,
            aoa=5.0,
            aos=0.5,
            heading=90.0,
            vertical_speed=2.0,
            turn_rate=5.0,
            bank_angle=10.0,
            aileron=0.1,
            elevator=-0.05,
            rudder=0.02,
        )

        props = CAMEncoder.encode_control_surfaces(telemetry)

        self.assertEqual(props[CAMKeys.CONTROL_AILERON], 0.1)
        self.assertEqual(props[CAMKeys.CONTROL_ELEVATOR], -0.05)
        self.assertEqual(props[CAMKeys.CONTROL_RUDDER], 0.02)

    def test_encode_angular_velocity(self):
        """Test encoding angular velocity."""
        angular_vel = (0.1, 0.2, 0.3)

        props = CAMEncoder.encode_angular_velocity(angular_vel)

        self.assertEqual(props[CAMKeys.ANGULAR_VEL_P], 0.1)
        self.assertEqual(props[CAMKeys.ANGULAR_VEL_Q], 0.2)
        self.assertEqual(props[CAMKeys.ANGULAR_VEL_R], 0.3)


class TestCAMDecoder(unittest.TestCase):
    """Test CAM decoding."""

    def test_decode_rl_metrics_basic(self):
        """Test decoding basic RL metrics."""
        props = {
            CAMKeys.REWARD_INSTANT: 1.5,
            CAMKeys.REWARD_CUM: 10.5,
            'Agent.Action.0': 0.1,
            'Agent.Action.1': 0.2,
        }

        metrics = CAMDecoder.decode_rl_metrics(props)

        self.assertEqual(metrics['reward'], 1.5)
        self.assertEqual(metrics['cumulative_reward'], 10.5)
        self.assertEqual(metrics['action'], [0.1, 0.2])

    def test_decode_rl_metrics_defaults(self):
        """Test decoding with missing values uses defaults."""
        props = {}

        metrics = CAMDecoder.decode_rl_metrics(props)

        self.assertEqual(metrics['reward'], 0.0)
        self.assertEqual(metrics['cumulative_reward'], 0.0)
        self.assertEqual(metrics['action'], [0.0, 0.0, 0.0, 0.5])

    def test_decode_reward_components(self):
        """Test decoding reward components."""
        props = {
            CAMKeys.REWARD_INSTANT: 1.0,
            'Agent.Reward.Tracking': 0.8,
            'Agent.Reward.Stability': 0.2,
        }

        metrics = CAMDecoder.decode_rl_metrics(props)

        self.assertIn('reward_components', metrics)
        self.assertEqual(metrics['reward_components']['tracking'], 0.8)
        self.assertEqual(metrics['reward_components']['stability'], 0.2)

    def test_decode_control_surfaces(self):
        """Test decoding control surfaces."""
        props = {
            CAMKeys.CONTROL_AILERON: 0.1,
            CAMKeys.CONTROL_ELEVATOR: -0.05,
            CAMKeys.CONTROL_RUDDER: 0.02,
        }

        controls = CAMDecoder.decode_control_surfaces(props)

        self.assertEqual(controls['aileron'], 0.1)
        self.assertEqual(controls['elevator'], -0.05)
        self.assertEqual(controls['rudder'], 0.02)

    def test_decode_angular_velocity(self):
        """Test decoding angular velocity."""
        props = {
            CAMKeys.ANGULAR_VEL_P: 0.1,
            CAMKeys.ANGULAR_VEL_Q: 0.2,
            CAMKeys.ANGULAR_VEL_R: 0.3,
        }

        angular_vel = CAMDecoder.decode_angular_velocity(props)

        self.assertEqual(angular_vel, (0.1, 0.2, 0.3))

    def test_decode_episode_metadata(self):
        """Test decoding episode metadata."""
        props = {
            CAMKeys.EPISODE_ID: 'episode_42',
            CAMKeys.EPISODE_NUM: 42,
            CAMKeys.TAGS: 'training,phase2',
            CAMKeys.SUCCESS: 'true',
            CAMKeys.TERM_REASON: 'completed',
            'Agent.Config.policy': 'PPO',
        }

        metadata = CAMDecoder.decode_episode_metadata(props)

        self.assertEqual(metadata['episode_id'], 'episode_42')
        self.assertEqual(metadata['episode_number'], 42)
        self.assertEqual(metadata['tags'], ['training', 'phase2'])
        self.assertEqual(metadata['success'], True)
        self.assertEqual(metadata['termination_reason'], 'completed')
        self.assertIn('config', metadata)
        self.assertEqual(metadata['config']['policy'], 'PPO')


if __name__ == '__main__':
    unittest.main()
