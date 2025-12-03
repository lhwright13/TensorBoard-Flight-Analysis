"""Custom Agent Metadata (CAM) schema for ACMI format.

This module implements the CAM addendum specification for embedding RL/AI metadata
in ACMI files using the Agent.* key namespace.

The CAM addendum is fully backward-compatible with standard ACMI viewers (Tacview),
which simply ignore unknown properties.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class CAMKeys:
    """Canonical CAM property keys following the addendum specification.

    All keys use the Agent. prefix to avoid collisions with standard ACMI properties.
    """

    # RL Metrics - Core
    REWARD_INSTANT = "Agent.Reward.Instant"
    REWARD_CUM = "Agent.Reward.Cum"
    VALUE = "Agent.Value"
    LOG_PROB = "Agent.LogProb"
    ADVANTAGE = "Agent.Advantage"
    ENTROPY = "Agent.Entropy"

    # Action encoding: Agent.Action.0, Agent.Action.1, ...
    ACTION_PREFIX = "Agent.Action"

    # Reward components: Agent.Reward.<ComponentName>
    REWARD_COMPONENT_PREFIX = "Agent.Reward"

    # Control surfaces (not in standard ACMI)
    CONTROL_AILERON = "Agent.Control.Aileron"
    CONTROL_ELEVATOR = "Agent.Control.Elevator"
    CONTROL_RUDDER = "Agent.Control.Rudder"

    # Angular velocity (body rates in rad/s)
    ANGULAR_VEL_P = "Agent.AngularVel.P"
    ANGULAR_VEL_Q = "Agent.AngularVel.Q"
    ANGULAR_VEL_R = "Agent.AngularVel.R"

    # G-force (not standard ACMI)
    G_FORCE = "Agent.GForce"

    # Episode metadata (sparse - only on specific records)
    EPISODE_ID = "Agent.EpisodeID"
    EPISODE_NUM = "Agent.EpisodeNum"
    SUCCESS = "Agent.Success"
    TERM_REASON = "Agent.TermReason"

    # Tags (comma-separated list)
    TAGS = "Agent.Tags"

    # Config dict: Agent.Config.<key>
    CONFIG_PREFIX = "Agent.Config"

    # Policy/model versioning
    POLICY = "Agent.Policy"
    POLICY_VER = "Agent.PolicyVer"
    MODEL_SHA = "Agent.ModelSHA"

    # Event severity
    EVENT_SEVERITY = "Agent.Event.Severity"

    # Strategy (for hierarchical control)
    STRATEGY = "Agent.Strategy"
    PLAN_L1 = "Agent.Plan.L1"
    PLAN_L2 = "Agent.Plan.L2"
    PLAN_L3 = "Agent.Plan.L3"
    PLAN_PATH = "Agent.Plan.Path"

    # Confidence (for uncertainty-aware agents)
    CONFIDENCE = "Agent.Confidence"
    CONFIDENCE_STD = "Agent.ConfidenceStd"


class CAMEncoder:
    """Encode Flight Plugin data structures to CAM properties.

    This class converts from the plugin's internal schema to ACMI CAM key-value pairs.
    """

    @staticmethod
    def encode_rl_metrics(rl_metrics) -> Dict[str, Any]:
        """Convert RLMetrics dataclass to CAM properties.

        Args:
            rl_metrics: RLMetrics instance from schema.py

        Returns:
            Dictionary of CAM properties
        """
        props = {}

        # Core metrics
        props[CAMKeys.REWARD_INSTANT] = float(rl_metrics.reward)
        props[CAMKeys.REWARD_CUM] = float(rl_metrics.cumulative_reward)

        # Action array -> Agent.Action.0, Agent.Action.1, ...
        for i, action_val in enumerate(rl_metrics.action):
            props[f"{CAMKeys.ACTION_PREFIX}.{i}"] = float(action_val)

        # Optional metrics
        if rl_metrics.value_estimate is not None:
            props[CAMKeys.VALUE] = float(rl_metrics.value_estimate)
        if rl_metrics.policy_logprob is not None:
            props[CAMKeys.LOG_PROB] = float(rl_metrics.policy_logprob)
        if rl_metrics.advantage is not None:
            props[CAMKeys.ADVANTAGE] = float(rl_metrics.advantage)
        if rl_metrics.entropy is not None:
            props[CAMKeys.ENTROPY] = float(rl_metrics.entropy)

        # Reward components dict -> Agent.Reward.<Component>
        if rl_metrics.reward_components:
            for component, value in rl_metrics.reward_components.items():
                # Capitalize first letter for consistency
                component_key = component.replace("_", "").capitalize()
                key = f"{CAMKeys.REWARD_COMPONENT_PREFIX}.{component_key}"
                props[key] = float(value)

        return props

    @staticmethod
    def encode_control_surfaces(telemetry) -> Dict[str, Any]:
        """Encode control surface positions to CAM properties.

        Args:
            telemetry: Telemetry dataclass from schema.py

        Returns:
            Dictionary of control surface CAM properties
        """
        props = {}

        if telemetry.aileron is not None:
            props[CAMKeys.CONTROL_AILERON] = float(telemetry.aileron)
        if telemetry.elevator is not None:
            props[CAMKeys.CONTROL_ELEVATOR] = float(telemetry.elevator)
        if telemetry.rudder is not None:
            props[CAMKeys.CONTROL_RUDDER] = float(telemetry.rudder)

        return props

    @staticmethod
    def encode_angular_velocity(angular_vel: tuple) -> Dict[str, Any]:
        """Encode body rates (p, q, r) to CAM properties.

        Args:
            angular_vel: Tuple of (p, q, r) in rad/s

        Returns:
            Dictionary of angular velocity CAM properties
        """
        p, q, r = angular_vel
        return {
            CAMKeys.ANGULAR_VEL_P: float(p),
            CAMKeys.ANGULAR_VEL_Q: float(q),
            CAMKeys.ANGULAR_VEL_R: float(r),
        }

    @staticmethod
    def encode_episode_metadata(episode) -> Dict[str, Any]:
        """Encode episode-level metadata (for first record).

        Args:
            episode: FlightEpisode instance

        Returns:
            Dictionary of episode metadata CAM properties
        """
        props = {
            CAMKeys.EPISODE_ID: str(episode.episode_id),
            CAMKeys.EPISODE_NUM: int(episode.episode_number),
        }

        # Tags as comma-separated string
        if episode.tags:
            props[CAMKeys.TAGS] = ",".join(episode.tags)

        # Config dict -> Agent.Config.key
        if episode.config:
            for key, value in episode.config.items():
                props[f"{CAMKeys.CONFIG_PREFIX}.{key}"] = value

        return props

    @staticmethod
    def encode_episode_termination(episode) -> Dict[str, Any]:
        """Encode termination metadata (for last record).

        Args:
            episode: FlightEpisode instance

        Returns:
            Dictionary of termination CAM properties
        """
        return {
            CAMKeys.SUCCESS: episode.success,
            CAMKeys.TERM_REASON: str(episode.termination_reason),
        }

    @staticmethod
    def encode_g_force(g_force: float) -> Dict[str, Any]:
        """Encode G-force to CAM property.

        Args:
            g_force: G-force value

        Returns:
            Dictionary with G-force CAM property
        """
        return {CAMKeys.G_FORCE: float(g_force)}


class CAMDecoder:
    """Decode CAM properties to Flight Plugin data structures.

    This class converts from ACMI CAM key-value pairs to the plugin's internal schema.
    """

    @staticmethod
    def decode_rl_metrics(props: Dict[str, Any]) -> Dict[str, Any]:
        """Extract RL metrics from CAM properties.

        Args:
            props: Dictionary of ACMI properties (may contain CAM keys)

        Returns:
            Dictionary suitable for creating RLMetrics dataclass
        """
        metrics = {}

        # Core metrics
        if CAMKeys.REWARD_INSTANT in props:
            metrics['reward'] = float(props[CAMKeys.REWARD_INSTANT])
        else:
            metrics['reward'] = 0.0  # Default if not present

        if CAMKeys.REWARD_CUM in props:
            metrics['cumulative_reward'] = float(props[CAMKeys.REWARD_CUM])
        else:
            metrics['cumulative_reward'] = 0.0

        # Action array - collect Agent.Action.N
        action = []
        i = 0
        while f"{CAMKeys.ACTION_PREFIX}.{i}" in props:
            action.append(float(props[f"{CAMKeys.ACTION_PREFIX}.{i}"]))
            i += 1

        if action:
            metrics['action'] = action
        else:
            # Default action if not present
            metrics['action'] = [0.0, 0.0, 0.0, 0.5]

        # Optional metrics
        if CAMKeys.VALUE in props:
            metrics['value_estimate'] = float(props[CAMKeys.VALUE])
        if CAMKeys.LOG_PROB in props:
            metrics['policy_logprob'] = float(props[CAMKeys.LOG_PROB])
        if CAMKeys.ADVANTAGE in props:
            metrics['advantage'] = float(props[CAMKeys.ADVANTAGE])
        if CAMKeys.ENTROPY in props:
            metrics['entropy'] = float(props[CAMKeys.ENTROPY])

        # Reward components - find all Agent.Reward.<Component>
        # Skip REWARD_INSTANT and REWARD_CUM
        reward_components = {}
        for key, value in props.items():
            if key.startswith(f"{CAMKeys.REWARD_COMPONENT_PREFIX}."):
                # Skip the core metrics
                if key not in [CAMKeys.REWARD_INSTANT, CAMKeys.REWARD_CUM]:
                    component = key.split('.')[-1].lower()
                    reward_components[component] = float(value)

        if reward_components:
            metrics['reward_components'] = reward_components

        return metrics

    @staticmethod
    def decode_control_surfaces(props: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """Extract control surface data from CAM properties.

        Args:
            props: Dictionary of ACMI properties

        Returns:
            Dictionary with aileron, elevator, rudder values (or None)
        """
        controls = {}

        if CAMKeys.CONTROL_AILERON in props:
            controls['aileron'] = float(props[CAMKeys.CONTROL_AILERON])
        if CAMKeys.CONTROL_ELEVATOR in props:
            controls['elevator'] = float(props[CAMKeys.CONTROL_ELEVATOR])
        if CAMKeys.CONTROL_RUDDER in props:
            controls['rudder'] = float(props[CAMKeys.CONTROL_RUDDER])

        return controls

    @staticmethod
    def decode_angular_velocity(props: Dict[str, Any]) -> tuple:
        """Extract body rates from CAM properties.

        Args:
            props: Dictionary of ACMI properties

        Returns:
            Tuple of (p, q, r) in rad/s
        """
        p = float(props.get(CAMKeys.ANGULAR_VEL_P, 0.0))
        q = float(props.get(CAMKeys.ANGULAR_VEL_Q, 0.0))
        r = float(props.get(CAMKeys.ANGULAR_VEL_R, 0.0))
        return (p, q, r)

    @staticmethod
    def decode_episode_metadata(props: Dict[str, Any]) -> Dict[str, Any]:
        """Extract episode metadata from CAM properties.

        Args:
            props: Dictionary of ACMI properties

        Returns:
            Dictionary with episode metadata
        """
        metadata = {}

        if CAMKeys.EPISODE_ID in props:
            metadata['episode_id'] = str(props[CAMKeys.EPISODE_ID])
        if CAMKeys.EPISODE_NUM in props:
            metadata['episode_number'] = int(props[CAMKeys.EPISODE_NUM])

        # Tags
        if CAMKeys.TAGS in props:
            tags_str = str(props[CAMKeys.TAGS]).strip('"')
            metadata['tags'] = [tag.strip() for tag in tags_str.split(',')]

        # Config dict - collect Agent.Config.*
        config = {}
        for key, value in props.items():
            if key.startswith(f"{CAMKeys.CONFIG_PREFIX}."):
                config_key = key.split('.')[-1]
                config[config_key] = value
        if config:
            metadata['config'] = config

        # Termination
        if CAMKeys.SUCCESS in props:
            success_val = props[CAMKeys.SUCCESS]
            if isinstance(success_val, str):
                metadata['success'] = success_val.lower() == 'true'
            else:
                metadata['success'] = bool(success_val)

        if CAMKeys.TERM_REASON in props:
            metadata['termination_reason'] = str(props[CAMKeys.TERM_REASON]).strip('"')

        return metadata

    @staticmethod
    def decode_g_force(props: Dict[str, Any]) -> float:
        """Extract G-force from CAM properties.

        Args:
            props: Dictionary of ACMI properties

        Returns:
            G-force value (default 1.0 if not present)
        """
        return float(props.get(CAMKeys.G_FORCE, 1.0))
