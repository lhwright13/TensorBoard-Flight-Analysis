#!/usr/bin/env python3
"""Extract test data from logged TensorBoard events for frontend testing."""

import json
import sys
from pathlib import Path
from tensorboard.backend.event_processing import event_accumulator

def extract_flight_data(log_dir: str, output_file: str = "src/frontend/test-data.js"):
    """Extract flight episode data from TensorBoard events.

    Args:
        log_dir: Path to TensorBoard log directory
        output_file: Output JavaScript file path
    """
    print(f"Loading events from: {log_dir}")

    # Load event files directly using protobuf
    from pathlib import Path
    from tensorboard.compat.proto.event_pb2 import Event

    event_files = list(Path(log_dir).glob("events.out.tfevents.*"))

    if not event_files:
        print("No event files found!")
        return

    # Read the most recent event file
    event_file = sorted(event_files)[-1]
    print(f"Reading: {event_file}")

    episode_data = None

    # Read events from the file using TFRecord format
    import struct

    with open(event_file, 'rb') as f:
        while True:
            # Read length (8 bytes: uint64)
            length_bytes = f.read(8)
            if not length_bytes:
                break

            length = struct.unpack('<Q', length_bytes)[0]

            # Read CRC (4 bytes)
            f.read(4)

            # Read data
            data = f.read(length)

            # Read data CRC (4 bytes)
            f.read(4)

            # Parse event
            event = Event()
            event.ParseFromString(data)

            # Check if this event has summary data
            if event.HasField('summary'):
                for value in event.summary.value:
                    # Look for flight plugin data
                    if value.tag.startswith('flight/'):
                        if value.HasField('metadata'):
                            plugin_data = value.metadata.plugin_data
                            if plugin_data.plugin_name == 'flight':
                                content = plugin_data.content
                                episode_data = json.loads(content.decode('utf-8'))
                                print(f"Found flight data in tag: {value.tag}")
                                break

                if episode_data:
                    break

    if not episode_data:
        print("Could not extract episode data from events!")
        return

    print(f"Extracted episode: {episode_data['episode_id']}")
    print(f"  Steps: {episode_data['total_steps']}")
    print(f"  Reward: {episode_data['total_reward']}")
    print(f"  Duration: {episode_data['duration']:.2f}s")

    # Write to JavaScript file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("// Auto-generated test data from logged flight episode\n")
        f.write("window.testFlightData = ")
        json.dump(episode_data, f, indent=2)
        f.write(";\n")

    print(f"\nTest data written to: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    else:
        log_dir = "learned_controllers/logs/flight_test"

    extract_flight_data(log_dir)
