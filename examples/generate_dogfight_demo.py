#!/usr/bin/env python3
"""Generate a dynamic dogfight demo showcasing multi-agent flight visualization.

This creates two aircraft engaged in pursuit/evasion maneuvers:
- Aggressor (Red): Pursuing aircraft with aggressive maneuvers
- Defender (Blue): Evading aircraft with defensive maneuvers

The scenario demonstrates:
- Multi-agent tracking and comparison
- Dynamic 3D flight paths with realistic maneuvers
- Full telemetry and RL metrics logging
- ACMI export for Tacview visualization
"""

import numpy as np
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tensorboard_flight import FlightLogger


def sigmoid(x, k=1.0):
    """Smooth transition function."""
    return 1 / (1 + np.exp(-k * x))


def smooth_transition(t, t_start, duration, start_val, end_val):
    """Smoothly interpolate between values."""
    if t < t_start:
        return start_val
    elif t > t_start + duration:
        return end_val
    else:
        progress = (t - t_start) / duration
        # Smooth step
        progress = progress * progress * (3 - 2 * progress)
        return start_val + (end_val - start_val) * progress


class AircraftState:
    """Track aircraft state for realistic physics."""

    def __init__(self, name, x, y, z, heading, speed):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.heading = heading  # degrees
        self.pitch = 0.0
        self.roll = 0.0
        self.speed = speed  # m/s
        self.throttle = 0.7

    def get_position(self):
        return (self.x, self.y, self.z)

    def get_orientation(self):
        return (self.roll, self.pitch, self.heading)

    def get_velocity(self):
        """Calculate velocity from heading and speed."""
        heading_rad = np.radians(self.heading)
        pitch_rad = np.radians(self.pitch)
        vx = self.speed * np.cos(heading_rad) * np.cos(pitch_rad)
        vy = self.speed * np.sin(heading_rad) * np.cos(pitch_rad)
        vz = self.speed * np.sin(pitch_rad)
        return (vx, vy, vz)


def generate_dogfight_scenario(duration=60.0, dt=0.05):
    """Generate a dynamic dogfight between two aircraft.

    Scenario phases:
    1. Initial approach (0-10s): Aggressor closing on defender's 6 o'clock
    2. Defensive break (10-20s): Defender executes hard break turn
    3. Pursuit curves (20-35s): Aggressor follows, both maneuvering
    4. Vertical fight (35-45s): Defender goes vertical, aggressor follows
    5. Rolling scissors (45-55s): Close-in maneuvering
    6. Separation (55-60s): Aircraft separate

    Returns:
        Tuple of (aggressor_data, defender_data)
    """
    steps = int(duration / dt)
    aggressor_data = []
    defender_data = []

    # Initial positions
    # Defender starts ahead, aggressor behind and slightly offset
    defender = AircraftState("defender", x=0, y=0, z=500, heading=0, speed=150)
    aggressor = AircraftState("aggressor", x=-800, y=50, z=480, heading=5, speed=180)

    for i in range(steps):
        t = i * dt

        # ===== PHASE 1: Initial Approach (0-10s) =====
        if t < 10:
            # Defender: Straight and level, unaware
            defender.pitch = 0
            defender.roll = 0
            defender.speed = 150

            # Aggressor: Closing in, slight lead pursuit
            dx = defender.x - aggressor.x
            dy = defender.y - aggressor.y
            target_heading = np.degrees(np.arctan2(dy, dx))
            aggressor.heading = smooth_transition(t, 0, 5, aggressor.heading, target_heading)
            aggressor.speed = 180
            aggressor.roll = (target_heading - aggressor.heading) * 0.5

        # ===== PHASE 2: Defensive Break (10-20s) =====
        elif t < 20:
            phase_t = t - 10

            # Defender: Hard right break with pull
            defender.roll = smooth_transition(phase_t, 0, 1, 0, 70)  # 70 deg bank
            turn_rate = 15 * (defender.roll / 70)  # deg/s based on bank
            defender.heading += turn_rate * dt
            defender.pitch = smooth_transition(phase_t, 0, 2, 0, 8)  # Pull up
            defender.speed = max(120, defender.speed - 10 * dt)  # Bleed speed in turn
            defender.throttle = 1.0  # Full power

            # Aggressor: Lag pursuit, trying to follow
            dx = defender.x - aggressor.x
            dy = defender.y - aggressor.y
            target_heading = np.degrees(np.arctan2(dy, dx))
            heading_diff = (target_heading - aggressor.heading + 180) % 360 - 180
            aggressor.heading += np.clip(heading_diff * 0.1, -12, 12) * dt * 60
            aggressor.roll = np.clip(heading_diff * 2, -60, 60)
            aggressor.pitch = smooth_transition(phase_t, 1, 2, 0, 5)
            aggressor.speed = max(140, aggressor.speed - 5 * dt)

        # ===== PHASE 3: Pursuit Curves (20-35s) =====
        elif t < 35:
            phase_t = t - 20

            # Defender: Reversing turns, trying to shake pursuit
            turn_period = 5.0  # seconds per turn reversal
            turn_direction = np.sin(2 * np.pi * phase_t / turn_period)
            defender.roll = 60 * turn_direction
            turn_rate = 12 * turn_direction
            defender.heading += turn_rate * dt
            defender.pitch = 3 + 5 * np.sin(phase_t * 0.5)  # Slight climb/dive
            defender.speed = 130 + 10 * np.cos(phase_t * 0.3)
            defender.throttle = 0.9 + 0.1 * np.sin(phase_t)

            # Aggressor: Pure pursuit with lead
            dx = defender.x - aggressor.x
            dy = defender.y - aggressor.y
            dz = defender.z - aggressor.z
            target_heading = np.degrees(np.arctan2(dy, dx))
            target_pitch = np.degrees(np.arctan2(dz, np.sqrt(dx**2 + dy**2)))

            heading_diff = (target_heading - aggressor.heading + 180) % 360 - 180
            aggressor.heading += np.clip(heading_diff * 0.15, -15, 15) * dt * 60
            aggressor.roll = np.clip(heading_diff * 2.5, -70, 70)
            pitch_diff = target_pitch - aggressor.pitch
            aggressor.pitch += np.clip(pitch_diff * 0.1, -5, 5) * dt * 60
            aggressor.speed = 160

        # ===== PHASE 4: Vertical Fight (35-45s) =====
        elif t < 45:
            phase_t = t - 35

            # Defender: Goes vertical, then over the top
            if phase_t < 5:
                # Climb
                defender.pitch = smooth_transition(phase_t, 0, 2, defender.pitch, 60)
                defender.roll = smooth_transition(phase_t, 0, 1, defender.roll, 0)
                defender.speed = max(100, defender.speed - 15 * dt)
            else:
                # Over the top and reverse
                defender.pitch = smooth_transition(phase_t, 5, 3, 60, -30)
                defender.heading += 20 * dt  # Heading change at top
                defender.roll = smooth_transition(phase_t, 5, 2, 0, -45)
                defender.speed = min(160, defender.speed + 20 * dt)
            defender.throttle = 1.0

            # Aggressor: Following into vertical
            dx = defender.x - aggressor.x
            dy = defender.y - aggressor.y
            dz = defender.z - aggressor.z
            target_pitch = np.degrees(np.arctan2(dz, np.sqrt(dx**2 + dy**2)))
            target_heading = np.degrees(np.arctan2(dy, dx))

            heading_diff = (target_heading - aggressor.heading + 180) % 360 - 180
            aggressor.heading += np.clip(heading_diff * 0.12, -10, 10) * dt * 60

            pitch_diff = target_pitch - aggressor.pitch
            aggressor.pitch = smooth_transition(phase_t, 0.5, 2, aggressor.pitch,
                                                aggressor.pitch + np.clip(pitch_diff, -40, 40))
            aggressor.roll = np.clip(heading_diff * 2, -50, 50)
            aggressor.speed = max(90, 160 - 10 * phase_t)

        # ===== PHASE 5: Rolling Scissors (45-55s) =====
        elif t < 55:
            phase_t = t - 45

            # Both aircraft in close, alternating rolls
            scissor_freq = 0.4  # Hz

            # Defender
            defender.roll = 80 * np.sin(2 * np.pi * scissor_freq * phase_t)
            defender.heading += 8 * np.cos(2 * np.pi * scissor_freq * phase_t) * dt
            defender.pitch = 10 + 15 * np.sin(2 * np.pi * scissor_freq * phase_t * 0.5)
            defender.speed = 110 + 20 * np.sin(phase_t * 0.5)
            defender.throttle = 0.7 + 0.3 * np.abs(np.sin(phase_t))

            # Aggressor: Counter-rolling
            aggressor.roll = 75 * np.sin(2 * np.pi * scissor_freq * phase_t + np.pi * 0.3)
            aggressor.heading += 7 * np.cos(2 * np.pi * scissor_freq * phase_t + 0.5) * dt
            aggressor.pitch = 8 + 12 * np.sin(2 * np.pi * scissor_freq * phase_t * 0.5 + 0.3)
            aggressor.speed = 115 + 15 * np.sin(phase_t * 0.5 + 0.2)
            aggressor.throttle = 0.8 + 0.2 * np.abs(np.cos(phase_t))

        # ===== PHASE 6: Separation (55-60s) =====
        else:
            phase_t = t - 55

            # Defender: Break away, dive and accelerate
            defender.roll = smooth_transition(phase_t, 0, 1, defender.roll, -30)
            defender.pitch = smooth_transition(phase_t, 0, 2, defender.pitch, -15)
            defender.heading += 5 * dt
            defender.speed = min(180, defender.speed + 20 * dt)
            defender.throttle = 1.0

            # Aggressor: Break opposite direction
            aggressor.roll = smooth_transition(phase_t, 0, 1, aggressor.roll, 25)
            aggressor.pitch = smooth_transition(phase_t, 0, 2, aggressor.pitch, -10)
            aggressor.heading -= 5 * dt
            aggressor.speed = min(175, aggressor.speed + 15 * dt)
            aggressor.throttle = 0.95

        # ===== Update Positions =====
        for aircraft in [defender, aggressor]:
            vx, vy, vz = aircraft.get_velocity()
            aircraft.x += vx * dt
            aircraft.y += vy * dt
            aircraft.z += vz * dt
            # Keep altitude reasonable
            aircraft.z = max(200, min(2000, aircraft.z))

        # ===== Calculate Distance =====
        dx = defender.x - aggressor.x
        dy = defender.y - aggressor.y
        dz = defender.z - aggressor.z
        distance = np.sqrt(dx**2 + dy**2 + dz**2)

        # ===== Generate Telemetry =====
        for aircraft, data_list, is_aggressor in [
            (aggressor, aggressor_data, True),
            (defender, defender_data, False)
        ]:
            vx, vy, vz = aircraft.get_velocity()
            airspeed = np.sqrt(vx**2 + vy**2 + vz**2)

            # G-force estimate based on turn rate and pitch rate
            turn_g = (aircraft.speed * np.radians(abs(aircraft.roll) * 0.2)) / 9.81
            pull_g = 1.0 + abs(aircraft.pitch) * 0.05
            g_force = max(1.0, min(9.0, pull_g + turn_g * 0.3))

            # Angle of attack (simplified)
            aoa = aircraft.pitch + np.random.normal(0, 0.5)
            if abs(aircraft.roll) > 45:
                aoa += 3  # Higher AoA in hard turns

            telemetry = {
                'airspeed': float(airspeed),
                'altitude': float(aircraft.z),
                'vertical_speed': float(vz),
                'heading': float(aircraft.heading % 360),
                'bank_angle': float(aircraft.roll),
                'g_force': float(g_force),
                'aoa': float(np.clip(aoa, -5, 25)),
                'turn_rate': float(aircraft.roll * 0.2),
                'throttle': float(aircraft.throttle),
                'mach': float(airspeed / 340),  # Approximate
                'aileron': float(aircraft.roll / 90),
                'elevator': float(aircraft.pitch / 30),
                'rudder': float(np.sin(t * 0.5) * 0.1),
            }

            # RL metrics - different strategies for each aircraft
            if is_aggressor:
                # Aggressor: Reward for closing distance, penalty for losing sight
                base_reward = 1.0 - distance / 1000  # Closer = better
                angle_to_target = np.degrees(np.arctan2(dy, dx))
                angle_off = abs((angle_to_target - aircraft.heading + 180) % 360 - 180)
                tracking_bonus = max(0, 1 - angle_off / 90)
                reward = base_reward + tracking_bonus * 0.5
                action_label = "pursuit"
            else:
                # Defender: Reward for increasing distance, evading
                base_reward = distance / 500 - 1  # Further = better
                # Bonus for being out of aggressor's forward cone
                evasion_bonus = 0.5 if distance > 400 else 0
                reward = base_reward + evasion_bonus
                action_label = "evasion"

            cumulative_reward = reward * (i + 1) / 100

            rl_metrics = {
                'reward': float(np.clip(reward, -2, 2)),
                'cumulative_reward': float(cumulative_reward),
                'value_estimate': float(50 + reward * 20),
                'action': [
                    float(aircraft.roll / 90),
                    float(aircraft.pitch / 30),
                    float(np.sin(t * 0.5) * 0.1),
                    float(aircraft.throttle)
                ],
                'policy_entropy': float(0.5 + 0.3 * np.sin(t * 0.1)),
                'reward_components': {
                    'distance': float(base_reward * 0.6),
                    'tracking' if is_aggressor else 'evasion': float(reward - base_reward),
                    'energy': float(0.1 * (1 - abs(g_force - 1) / 8)),
                },
                'distance_to_opponent': float(distance),
            }

            data_list.append({
                'step': i,
                'timestamp': t,
                'position': aircraft.get_position(),
                'orientation': aircraft.get_orientation(),
                'velocity': aircraft.get_velocity(),
                'angular_velocity': (
                    float(np.sin(t) * 5),
                    float(np.cos(t) * 3),
                    float(aircraft.roll * 0.1)
                ),
                'telemetry': telemetry,
                'rl_metrics': rl_metrics,
            })

    return aggressor_data, defender_data


def main():
    """Generate dogfight demo and save to example_data/."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate dogfight demo data')
    parser.add_argument('--output', default='example_data/dogfight',
                        help='Output directory (default: example_data/dogfight)')
    parser.add_argument('--duration', type=float, default=60.0,
                        help='Scenario duration in seconds (default: 60)')
    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / args.output

    print("=" * 60)
    print("DOGFIGHT DEMO GENERATOR")
    print("=" * 60)
    print(f"\nGenerating {args.duration}s dogfight scenario...")

    # Generate flight data
    aggressor_data, defender_data = generate_dogfight_scenario(
        duration=args.duration,
        dt=0.05  # 20 Hz
    )

    print(f"Generated {len(aggressor_data)} timesteps per aircraft")

    # Create separate loggers for each agent (allows side-by-side comparison)
    aggressor_logger = FlightLogger(log_dir=str(output_dir / "aggressor"))
    defender_logger = FlightLogger(log_dir=str(output_dir / "defender"))

    # Log episodes
    print("\nLogging flight data...")
    aggressor_logger.start_episode(agent_id="aggressor")
    defender_logger.start_episode(agent_id="defender")

    for agg, dfn in zip(aggressor_data, defender_data):
        # Log aggressor
        aggressor_logger.log_flight_data(
            step=agg['step'],
            agent_id="aggressor",
            position=agg['position'],
            orientation=agg['orientation'],
            velocity=agg['velocity'],
            angular_velocity=agg['angular_velocity'],
            telemetry=agg['telemetry'],
            rl_metrics=agg['rl_metrics'],
            timestamp=agg['timestamp'],
        )

        # Log defender
        defender_logger.log_flight_data(
            step=dfn['step'],
            agent_id="defender",
            position=dfn['position'],
            orientation=dfn['orientation'],
            velocity=dfn['velocity'],
            angular_velocity=dfn['angular_velocity'],
            telemetry=dfn['telemetry'],
            rl_metrics=dfn['rl_metrics'],
            timestamp=dfn['timestamp'],
        )

    # End episodes
    aggressor_logger.end_episode(
        success=True,
        termination_reason="scenario_complete",
        config={'role': 'aggressor', 'strategy': 'pursuit'},
        tags=['demo', 'dogfight', 'aggressor'],
    )

    defender_logger.end_episode(
        success=True,
        termination_reason="scenario_complete",
        config={'role': 'defender', 'strategy': 'evasion'},
        tags=['demo', 'dogfight', 'defender'],
    )

    aggressor_logger.close()
    defender_logger.close()

    # Summary
    print("\n" + "=" * 60)
    print("DEMO DATA GENERATED")
    print("=" * 60)

    print(f"\nTensorBoard logs: {output_dir}/")
    print(f"  - aggressor/  (pursuit strategy)")
    print(f"  - defender/   (evasion strategy)")

    print("\n" + "-" * 60)
    print("TO VIEW THE DEMO:")
    print("-" * 60)
    print(f"\n1. Start TensorBoard:")
    print(f"   tensorboard --logdir {output_dir}")
    print(f"\n2. Open browser to http://localhost:6006")
    print(f"   Navigate to the 'Flight' tab")
    print(f"\n3. Select both runs to see both aircraft")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
