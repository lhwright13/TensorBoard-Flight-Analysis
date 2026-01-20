"""Stable-Baselines3 callbacks for flight logging."""

import numpy as np
from typing import Optional, Dict, Any
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import VecEnv

from tensorboard_flight import FlightLogger


class FlightLoggerCallback(BaseCallback):
    """SB3 callback that automatically logs flight trajectories.

    This callback captures flight data during training and logs it to
    TensorBoard using the FlightLogger. It works with any environment
    that provides the necessary flight data in observations or info dict.

    Example:
        >>> from tensorboard_flight.callbacks import FlightLoggerCallback
        >>> logger = FlightLogger(log_dir="runs/training")
        >>> callback = FlightLoggerCallback(logger, log_every_n_episodes=10)
        >>> model.learn(total_timesteps=100000, callback=callback)
    """

    def __init__(
        self,
        logger: FlightLogger,
        log_every_n_episodes: int = 1,
        agent_id: str = "sb3_agent",
        verbose: int = 0,
    ):
        """Initialize FlightLoggerCallback.

        Args:
            logger: FlightLogger instance
            log_every_n_episodes: Log every N episodes (default: 1 = all episodes)
            agent_id: Identifier for this agent
            verbose: Verbosity level
        """
        super().__init__(verbose)

        self.flight_logger = logger
        self.log_every_n_episodes = log_every_n_episodes
        self.agent_id = agent_id

        # Episode tracking
        self.episode_count = 0
        self.current_episode_started = False
        self.should_log_episode = False

        # Buffer for current episode
        self.episode_steps = []

    def _on_training_start(self) -> None:
        """Called before the first rollout starts."""
        if self.verbose > 0:
            print(f"FlightLoggerCallback: Starting flight logging for {self.agent_id}")

    def _on_rollout_start(self) -> None:
        """Called at the start of a rollout."""
        pass

    def _on_step(self) -> bool:
        """Called after each environment step.

        Returns:
            True to continue training
        """
        # Get environment
        env = self.training_env

        # Check if we're in a vectorized environment
        if isinstance(env, VecEnv):
            # Handle first environment only for simplicity
            env_idx = 0

            # Get done signal - we need this to track ALL episodes, not just logged ones
            done = self.locals.get('dones', [False])[env_idx]

            # Check if episode just started (after a done or at the very beginning)
            if not self.current_episode_started:
                # Decide if we should log this episode
                self.should_log_episode = (
                    self.episode_count % self.log_every_n_episodes == 0
                )

                if self.should_log_episode:
                    self.flight_logger.start_episode(agent_id=self.agent_id)
                    self.episode_steps = []

                    if self.verbose > 1:
                        print(f"  Started logging episode {self.episode_count}")

                # Mark episode as started regardless of logging
                self.current_episode_started = True

            # If we're logging this episode, capture the step data
            if self.should_log_episode:
                # Extract data from locals
                obs = self.locals.get('new_obs', [None])[env_idx]
                reward = self.locals.get('rewards', [0.0])[env_idx]
                info = self.locals.get('infos', [{}])[env_idx]
                action = self.locals.get('actions', [None])[env_idx]

                if obs is not None and action is not None:
                    # Extract flight data from observation or info
                    step_data = self._extract_flight_data(
                        obs, action, reward, info, self.num_timesteps
                    )

                    if step_data is not None:
                        # Log the data
                        self.flight_logger.log_flight_data(**step_data)
                        self.episode_steps.append(step_data)

            # Check if episode ended - this must happen for ALL episodes
            if done:
                # If we were logging this episode, finalize it
                if self.should_log_episode:
                    info = self.locals.get('infos', [{}])[env_idx]
                    success = info.get('success', False)
                    termination_reason = info.get('termination_reason', 'unknown')

                    self.flight_logger.end_episode(
                        success=success,
                        termination_reason=termination_reason,
                        config={'episode_num': self.episode_count},
                        tags=[f'training_step_{self.num_timesteps}'],
                    )

                    if self.verbose > 1:
                        total_reward = sum(s['rl_metrics']['reward']
                                          for s in self.episode_steps)
                        print(f"  Logged episode {self.episode_count}: "
                              f"{len(self.episode_steps)} steps, "
                              f"reward={total_reward:.2f}")

                    self.episode_steps = []

                # Always increment episode count and reset state
                self.current_episode_started = False
                self.should_log_episode = False
                self.episode_count += 1

        return True

    def _extract_flight_data(
        self,
        obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        info: Dict[str, Any],
        step: int,
    ) -> Optional[Dict[str, Any]]:
        """Extract flight data from environment step.

        This method needs to be customized based on your environment's
        observation space and info dict structure.

        Args:
            obs: Observation from environment
            action: Action taken
            reward: Reward received
            info: Info dict from environment
            step: Global step number

        Returns:
            Dictionary with flight data, or None if data unavailable
        """
        # Parse observation space (customize based on your env)
        # RateControlEnv observation:
        # [p, q, r, p_cmd, q_cmd, r_cmd, p_err, q_err, r_err,
        #  airspeed, altitude, roll, pitch, yaw,
        #  prev_aileron, prev_elevator, prev_rudder, prev_throttle]

        if len(obs) < 18:
            return None

        # Current rates
        p, q, r = obs[0], obs[1], obs[2]

        # Commanded rates
        p_cmd, q_cmd, r_cmd = obs[3], obs[4], obs[5]

        # Flight state
        airspeed = float(obs[9])
        altitude = float(obs[10])
        roll = float(obs[11])
        pitch = float(obs[12])
        yaw = float(obs[13])

        # Get position from info if available (otherwise use dummy values)
        # Position should be in NED coordinates - frontend handles transformation
        position = info.get('position', np.array([0.0, 0.0, -altitude]))
        if not isinstance(position, (list, np.ndarray)):
            position = np.array([0.0, 0.0, -altitude])
        position = tuple(float(x) for x in position[:3])

        # Velocity (approximate from airspeed and orientation in NED)
        vx = airspeed * np.cos(pitch) * np.cos(yaw)
        vy = airspeed * np.cos(pitch) * np.sin(yaw)
        vz = -airspeed * np.sin(pitch)  # NED: positive pitch = nose up = negative vz
        velocity = (float(vx), float(vy), float(vz))

        # Orientation in degrees (NED convention - frontend handles transformation)
        orientation = (
            float(np.degrees(roll)),
            float(np.degrees(pitch)),
            float(np.degrees(yaw)),
        )

        # Angular velocity (body rates)
        angular_velocity = (float(p), float(q), float(r))

        # Telemetry
        telemetry = {
            'airspeed': airspeed,
            'altitude': altitude,
            'g_force': 1.0,  # Could compute from info if available
            'throttle': float(action[3]) if len(action) > 3 else 0.5,
            'aoa': 0.0,  # Would need this from info
            'aos': 0.0,
            'heading': float(np.degrees(yaw)),
            'vertical_speed': float(vz),
            'turn_rate': float(r),
            'bank_angle': float(np.degrees(roll)),
            'aileron': float(action[0]) if len(action) > 0 else 0.0,
            'elevator': float(action[1]) if len(action) > 1 else 0.0,
            'rudder': float(action[2]) if len(action) > 2 else 0.0,
        }

        # RL metrics
        rl_metrics = {
            'reward': float(reward),
            'action': action.tolist() if isinstance(action, np.ndarray) else list(action),
            'value_estimate': info.get('value', None),
            'policy_logprob': info.get('log_prob', None),
        }

        # Add reward components if available
        if 'reward_components' in info:
            rl_metrics['reward_components'] = info['reward_components']

        # Events (if crash or important event)
        events = []
        if 'termination_reason' in info and info.get('dones', False):
            events.append({
                'timestamp': info.get('time', 0.0),
                'type': 'termination',
                'severity': 'error' if 'crash' in info['termination_reason'] else 'info',
                'message': info['termination_reason'],
            })

        return {
            'step': step,
            'agent_id': self.agent_id,
            'position': position,
            'orientation': orientation,
            'velocity': velocity,
            'angular_velocity': angular_velocity,
            'telemetry': telemetry,
            'rl_metrics': rl_metrics,
            'events': events if events else None,
            'timestamp': info.get('time', step * 0.02),  # Assume 50Hz if not available
        }

    def _on_rollout_end(self) -> None:
        """Called at the end of a rollout."""
        # Flush logger periodically
        self.flight_logger.flush()

    def _on_training_end(self) -> None:
        """Called at the end of training."""
        # Close any incomplete episode (only if we were actually logging it)
        if self.current_episode_started and self.should_log_episode:
            self.flight_logger.end_episode(termination_reason="training_ended")
        self.current_episode_started = False
        self.should_log_episode = False

        # Flush but don't close - logger may be reused in curriculum learning
        self.flight_logger.flush()

        if self.verbose > 0:
            print(f"FlightLoggerCallback: Logged {self.episode_count} episodes")
