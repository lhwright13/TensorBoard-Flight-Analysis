#!/usr/bin/env python3
"""Generate a synthetic flight episode for frontend testing."""

import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tensorboard_flight.logger import FlightLogger

def generate_straight_flight(duration=30.0, dt=0.1):
    """Generate a simple straight-line flight pattern for debugging.

    Aircraft flies straight along the +X axis with constant altitude,
    zero roll, zero pitch, and constant heading (90 degrees = pointing +Y).

    Args:
        duration: Flight duration in seconds
        dt: Time step in seconds
    """
    steps = int(duration / dt)

    # Straight flight parameters
    speed = 20.0  # m/s
    altitude = 50.0  # meters
    heading = 90.0  # degrees (pointing along +Y axis in XY plane)

    data = []

    for i in range(steps):
        t = i * dt

        # Position: straight line along +Y axis
        x = 0.0
        y = speed * t
        z = altitude

        # Velocity: constant along +Y
        vx = 0.0
        vy = speed
        vz = 0.0

        # Orientation: no roll, no pitch, constant heading
        roll = 0.0
        pitch = 0.0
        yaw = heading

        # Angular velocity: zero (no rotation)
        wx = 0.0
        wy = 0.0
        wz = 0.0

        # Telemetry
        airspeed = speed
        telemetry = {
            'airspeed': float(airspeed),
            'altitude': float(z),
            'vertical_speed': float(vz),
            'heading': float(yaw),
            'bank_angle': float(roll),
            'g_force': 1.0,
            'aoa': 0.0,
            'turn_rate': 0.0,
            'throttle': 0.7,
            'aileron': 0.0,
            'elevator': 0.0,
            'rudder': 0.0,
        }

        # RL metrics
        reward = 1.0
        cumulative_reward = reward * (i + 1)

        rl_metrics = {
            'reward': float(reward),
            'cumulative_reward': float(cumulative_reward),
            'value_estimate': 50.0,
            'action': [0.0, 0.0, 0.0, 0.7],
            'reward_components': {
                'altitude': 0.5,
                'speed': 0.3,
                'heading': 0.2,
            }
        }

        data.append({
            'step': i,
            'position': (float(x), float(y), float(z)),
            'orientation': (float(roll), float(pitch), float(yaw)),
            'velocity': (float(vx), float(vy), float(vz)),
            'angular_velocity': (float(wx), float(wy), float(wz)),
            'telemetry': telemetry,
            'rl_metrics': rl_metrics,
        })

    return data


def generate_circular_flight(duration=30.0, dt=0.1):
    """Generate a simple circular flight pattern.

    Args:
        duration: Flight duration in seconds
        dt: Time step in seconds
    """
    steps = int(duration / dt)

    # Circular path parameters
    radius = 100.0  # meters
    altitude = 50.0  # meters
    speed = 20.0    # m/s
    angular_velocity = speed / radius  # rad/s

    data = []

    for i in range(steps):
        t = i * dt
        angle = angular_velocity * t

        # Position: circular path
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = altitude + 5 * np.sin(2 * angle)  # Slight altitude variation

        # Velocity: tangent to circle
        vx = -speed * np.sin(angle)
        vy = speed * np.cos(angle)
        vz = 10 * np.cos(2 * angle) * angular_velocity  # Altitude rate

        # Orientation: banking into turn
        roll = 15.0 * np.sin(angle)  # Bank angle
        pitch = 5.0 * np.sin(2 * angle)  # Pitch variation
        # Yaw should match velocity direction - calculate from velocity vector
        yaw = np.degrees(np.arctan2(vy, vx))

        # Angular velocity
        wx = 0.1 * np.sin(t)
        wy = 0.1 * np.cos(t)
        wz = np.degrees(angular_velocity)  # Turn rate

        # Telemetry
        airspeed = np.sqrt(vx**2 + vy**2 + vz**2)
        telemetry = {
            'airspeed': float(airspeed),
            'altitude': float(z),
            'vertical_speed': float(vz),
            'heading': float((yaw + 360) % 360),  # Normalize to 0-360
            'bank_angle': float(roll),
            'g_force': float(1.0 + 0.2 * abs(np.sin(angle))),
            'aoa': float(5.0 + 2 * np.sin(t)),
            'turn_rate': float(wz),
            'throttle': float(0.7 + 0.1 * np.sin(t)),
            'aileron': float(roll / 30.0),
            'elevator': float(pitch / 20.0),
            'rudder': float(0.05 * np.sin(t)),
        }

        # RL metrics
        reward = 1.0 + 0.5 * np.sin(t)  # Varying reward
        cumulative_reward = reward * (i + 1) / steps * 100

        rl_metrics = {
            'reward': float(reward),
            'cumulative_reward': float(cumulative_reward),
            'value_estimate': float(50 + 10 * np.sin(t)),
            'action': [
                float(roll / 30.0),
                float(pitch / 20.0),
                float(0.05 * np.sin(t)),
                float(0.7 + 0.1 * np.sin(t))
            ],
            'reward_components': {
                'altitude': float(0.5 + 0.1 * np.sin(t)),
                'speed': float(0.3 + 0.1 * np.cos(t)),
                'heading': float(0.2),
            }
        }

        data.append({
            'step': i,
            'position': (float(x), float(y), float(z)),
            'orientation': (float(roll), float(pitch), float(yaw)),
            'velocity': (float(vx), float(vy), float(vz)),
            'angular_velocity': (float(wx), float(wy), float(wz)),
            'telemetry': telemetry,
            'rl_metrics': rl_metrics,
        })

    return data


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic flight test data')
    parser.add_argument('--mode', choices=['straight', 'circular'], default='straight',
                        help='Flight pattern to generate (default: straight for easier debugging)')
    args = parser.parse_args()

    print(f"Generating synthetic flight episode ({args.mode} pattern)...")

    # Create logger
    log_dir = "src/frontend/test_logs"
    logger = FlightLogger(log_dir=log_dir)

    # Generate flight data based on mode
    if args.mode == 'straight':
        flight_data = generate_straight_flight(duration=30.0, dt=0.1)
    else:
        flight_data = generate_circular_flight(duration=30.0, dt=0.1)

    print(f"Generated {len(flight_data)} timesteps ({args.mode} pattern)")

    # Start episode
    logger.start_episode(agent_id="test_agent")

    # Log all timesteps
    for data in flight_data:
        logger.log_flight_data(
            step=data['step'],
            agent_id="test_agent",
            position=data['position'],
            orientation=data['orientation'],
            velocity=data['velocity'],
            angular_velocity=data['angular_velocity'],
            telemetry=data['telemetry'],
            rl_metrics=data['rl_metrics'],
            timestamp=data['step'] * 0.1,
        )

    # End episode
    logger.end_episode(
        success=True,
        termination_reason="completed_pattern",
    )

    print(f"\nFlight episode logged to: {log_dir}")
    print(f"Total steps: {len(flight_data)}")
    print(f"Duration: {flight_data[-1]['step'] * 0.1:.1f}s")
    print("\nNow extracting test data...")

    # Extract test data
    from extract_test_data import extract_flight_data
    extract_flight_data(log_dir, output_file="src/frontend/test-data.js")

    print("\nDone! You can now open src/frontend/test.html in a browser.")


if __name__ == "__main__":
    main()
