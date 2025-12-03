#!/usr/bin/env python3
"""Example: ACMI integration with RL training.

This example shows how to use ACMILogger for automatic ACMI export
during Stable-Baselines3 training.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import gymnasium as gym
from tensorboard_flight.acmi import ACMILogger
from tensorboard_flight.data.schema import Telemetry, RLMetrics, Orientation
import numpy as np


def simulate_rl_training():
    """Simulate a simple RL training loop with ACMI export."""
    print("="*60)
    print("ACMI Integration Example")
    print("="*60)

    # Create ACMI-enabled logger
    logger = ACMILogger(
        log_dir="runs/acmi_example",
        enable_acmi_export=True,           # Enable ACMI generation
        acmi_dir="runs/acmi_example/acmi", # ACMI output directory
        acmi_export_interval=1,            # Export every episode
        acmi_prefix="example",
    )

    print(f"\nLogger created:")
    print(f"  TensorBoard logs: runs/acmi_example/")
    print(f"  ACMI files: runs/acmi_example/acmi/")

    # Simulate 3 episodes
    num_episodes = 3
    steps_per_episode = 100

    for episode in range(num_episodes):
        print(f"\nEpisode {episode + 1}/{num_episodes}")

        logger.start_episode(agent_id="demo_agent")

        # Simulate circular flight path
        for step in range(steps_per_episode):
            t = step * 0.02  # 50 Hz

            # Circular trajectory
            radius = 100.0
            angular_speed = 0.1  # rad/s

            x = radius * np.cos(angular_speed * t)
            y = radius * np.sin(angular_speed * t)
            z = 1000.0 + 10.0 * np.sin(0.1 * t)  # Gentle altitude variation

            # Velocity
            vx = -radius * angular_speed * np.sin(angular_speed * t)
            vy = radius * angular_speed * np.cos(angular_speed * t)
            vz = 10.0 * 0.1 * np.cos(0.1 * t)

            # Orientation (banking into turn)
            roll = np.degrees(np.arctan2(vy, vx) * 0.2)  # Bank angle
            pitch = np.degrees(np.arctan2(vz, np.sqrt(vx**2 + vy**2)))
            yaw = np.degrees(np.arctan2(vy, vx))

            # Airspeed
            airspeed = np.sqrt(vx**2 + vy**2 + vz**2)

            # Telemetry
            telemetry = {
                'airspeed': airspeed,
                'altitude': z,
                'g_force': 1.0 + 0.2 * np.abs(np.sin(angular_speed * t)),
                'throttle': 0.6 + 0.1 * np.sin(0.05 * t),
                'aoa': 5.0 + 2.0 * np.sin(0.2 * t),
                'aos': 0.5 * np.cos(0.3 * t),
                'heading': yaw,
                'vertical_speed': vz,
                'turn_rate': np.degrees(angular_speed),
                'bank_angle': roll,
            }

            # RL metrics (simulated)
            reward = 1.0 - 0.01 * np.abs(z - 1000.0)  # Reward for altitude hold

            rl_metrics = {
                'reward': reward,
                'action': [
                    0.1 * np.sin(0.2 * t),  # Aileron
                    0.05 * np.cos(0.3 * t),  # Elevator
                    0.02 * np.sin(0.4 * t),  # Rudder
                    telemetry['throttle'],   # Throttle
                ],
                'value_estimate': 50.0 + 10.0 * np.sin(0.1 * t),
                'policy_logprob': -1.5,
                'entropy': 0.8,
                'reward_components': {
                    'altitude': 0.6 * reward,
                    'stability': 0.3 * reward,
                    'efficiency': 0.1 * reward,
                }
            }

            # Log to both TensorBoard and ACMI
            logger.log_flight_data(
                step=step,
                agent_id="demo_agent",
                position=(x, y, z),
                orientation=(roll, pitch, yaw),
                velocity=(vx, vy, vz),
                telemetry=telemetry,
                rl_metrics=rl_metrics,
                timestamp=t,
            )

        # End episode
        success = episode % 2 == 0  # Alternate success/failure
        logger.end_episode(
            success=success,
            termination_reason="completed" if success else "timeout",
            config={'policy': 'PPO', 'learning_rate': 0.0003},
            tags=['example', f'episode_{episode}'],
        )

        print(f"  Logged {steps_per_episode} steps")

    # Close logger
    logger.close()

    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)

    # Show created files
    acmi_files = logger.get_acmi_files()
    print(f"\nCreated {len(acmi_files)} ACMI files:")
    for acmi_file in acmi_files:
        size_kb = acmi_file.stat().st_size / 1024
        print(f"  {acmi_file.name} ({size_kb:.1f} KB)")

    print("\nNext steps:")
    print("  1. View in TensorBoard:")
    print("     tensorboard --logdir runs/acmi_example")
    print("     Navigate to the 'Flight' tab")
    print()
    print("  2. View ACMI in Tacview (if installed):")
    print(f"     tacview {acmi_files[0]}")
    print()
    print("  3. Import ACMI to different TensorBoard instance:")
    print("     python -m tensorboard_flight.acmi import \\")
    print(f"         {acmi_files[0]} --output runs/imported")
    print()
    print("  4. Inspect ACMI file:")
    print("     python -m tensorboard_flight.acmi info \\")
    print(f"         {acmi_files[0]}")


def main():
    """Run example."""
    try:
        simulate_rl_training()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
