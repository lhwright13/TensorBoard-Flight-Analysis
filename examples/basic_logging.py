"""Basic example of using FlightLogger.

This example demonstrates how to log flight data to TensorBoard
using the FlightLogger API.
"""

import numpy as np
from tensorboard_flight import FlightLogger


def simulate_flight_step(step):
    """Simulate a single flight step.

    Returns dummy data for demonstration purposes.
    """
    t = step * 0.01  # Time in seconds

    # Simple circular trajectory
    radius = 100.0
    height = 50.0 + 10.0 * np.sin(t * 0.1)

    x = radius * np.cos(t * 0.1)
    y = radius * np.sin(t * 0.1)
    z = height

    # Velocity
    vx = -radius * 0.1 * np.sin(t * 0.1)
    vy = radius * 0.1 * np.cos(t * 0.1)
    vz = 10.0 * 0.1 * np.cos(t * 0.1)

    # Orientation (bank into turn)
    roll = np.degrees(np.arctan2(vy, vx)) * 0.2
    pitch = np.degrees(np.arctan2(vz, np.sqrt(vx**2 + vy**2)))
    yaw = np.degrees(np.arctan2(vy, vx))

    # Compute telemetry
    airspeed = np.sqrt(vx**2 + vy**2 + vz**2)

    telemetry = {
        'airspeed': airspeed,
        'altitude': z,
        'g_force': 1.0 + 0.1 * np.sin(t * 0.5),
        'throttle': 0.7 + 0.1 * np.sin(t * 0.3),
        'aoa': 5.0 + 2.0 * np.sin(t * 0.2),
        'aos': 0.5 * np.sin(t * 0.4),
        'heading': yaw,
        'vertical_speed': vz,
        'turn_rate': np.degrees(0.1),
        'bank_angle': roll,
    }

    # Dummy RL metrics
    reward = 1.0 - 0.01 * np.abs(height - 50.0)  # Reward for staying at target altitude
    action = [
        0.1 * np.sin(t * 0.2),  # Aileron
        0.05 * np.cos(t * 0.3),  # Elevator
        0.02 * np.sin(t * 0.4),  # Rudder
        0.7  # Throttle
    ]

    rl_metrics = {
        'reward': reward,
        'action': action,
        'value_estimate': 10.0 + 2.0 * np.sin(t * 0.1),
        'policy_logprob': -1.5,
        'entropy': 0.8,
    }

    return (x, y, z), (roll, pitch, yaw), (vx, vy, vz), telemetry, rl_metrics


def main():
    """Run basic logging example."""
    print("Starting flight logging example...")

    # Create logger
    logger = FlightLogger(
        log_dir="runs/basic_example",
        max_buffer_size=100,
    )

    # Simulate multiple episodes
    num_episodes = 5
    steps_per_episode = 500

    for episode in range(num_episodes):
        print(f"\nEpisode {episode + 1}/{num_episodes}")

        logger.start_episode(agent_id="example_agent")

        for step in range(steps_per_episode):
            # Simulate flight
            position, orientation, velocity, telemetry, rl_metrics = simulate_flight_step(
                episode * steps_per_episode + step
            )

            # Log data
            logger.log_flight_data(
                step=step,
                agent_id="example_agent",
                position=position,
                orientation=orientation,
                velocity=velocity,
                telemetry=telemetry,
                rl_metrics=rl_metrics,
            )

            if step % 100 == 0:
                print(f"  Step {step}/{steps_per_episode}")

        # End episode
        success = episode % 2 == 0  # Alternate success/failure
        logger.end_episode(
            success=success,
            termination_reason="completed" if success else "timeout",
            tags=["example", f"episode_{episode}"],
        )

    # Close logger
    logger.close()

    print("\n" + "="*60)
    print("Logging complete!")
    print("="*60)
    print("\nTo view the data in TensorBoard, run:")
    print("  tensorboard --logdir runs/basic_example")
    print("\nThen open your browser to http://localhost:6006")
    print("and navigate to the 'Flight' tab.")


if __name__ == "__main__":
    main()
