"""Command-line interface for ACMI import/export.

This module provides CLI tools for working with ACMI files from the command line.
"""

import argparse
import sys
from pathlib import Path

from .converter import import_acmi, batch_import_acmi, ACMIConverter
from .parser import ACMIParser


def cmd_import(args):
    """Import ACMI file to TensorBoard."""
    print(f"Importing ACMI file: {args.input}")
    print(f"Output directory: {args.output}")

    count = import_acmi(
        acmi_file=args.input,
        output_dir=args.output,
        agent_prefix=args.prefix,
    )

    print(f"\n✓ Successfully imported {count} episode(s)")
    print(f"\nTo view in TensorBoard:")
    print(f"  tensorboard --logdir {args.output}")
    print(f"  # Then navigate to the 'Flight' tab")


def cmd_batch_import(args):
    """Batch import multiple ACMI files."""
    print(f"Batch importing ACMI files from: {args.input_dir}")
    print(f"Output directory: {args.output}")
    print(f"Pattern: {args.pattern}")

    count = batch_import_acmi(
        acmi_dir=args.input_dir,
        output_dir=args.output,
        pattern=args.pattern,
    )

    print(f"\n✓ Successfully imported {count} total episode(s)")
    print(f"\nTo view in TensorBoard:")
    print(f"  tensorboard --logdir {args.output}")


def cmd_export(args):
    """Export TensorBoard episode to ACMI (placeholder)."""
    print("Export functionality requires plugin integration")
    print("Use ACMIConverter.episode_to_acmi() in Python code")
    print("\nExample:")
    print("  from tensorboard_flight.acmi import ACMIConverter")
    print("  converter = ACMIConverter()")
    print("  converter.episode_to_acmi(episode, 'output.txt.acmi')")


def cmd_info(args):
    """Display information about an ACMI file."""
    print(f"Parsing ACMI file: {args.input}")

    parser = ACMIParser()
    data = parser.parse_file(args.input)

    # Display file info
    print("\n" + "="*60)
    print("ACMI File Information")
    print("="*60)

    # Global properties
    print("\nGlobal Properties:")
    for key, value in data['global'].items():
        print(f"  {key}: {value}")

    # Objects
    print(f"\nObjects: {len(data['objects'])}")
    object_names = parser.get_all_object_names()
    for obj_id, name in object_names.items():
        state_count = len(data['objects'][obj_id])
        duration = 0.0
        if state_count > 0:
            first = data['objects'][obj_id][0]['timestamp']
            last = data['objects'][obj_id][-1]['timestamp']
            duration = last - first

        print(f"  {obj_id} ({name}): {state_count} states, {duration:.1f}s duration")

    # Events
    if data['events']:
        print(f"\nEvents: {len(data['events'])}")
        for event in data['events'][:5]:  # Show first 5
            print(f"  [{event['timestamp']:.1f}s] {event['type']}: {event.get('message', '')}")
        if len(data['events']) > 5:
            print(f"  ... and {len(data['events']) - 5} more")

    # Check for CAM metadata
    print("\nCAM Metadata Detection:")
    has_cam = False
    cam_keys = set()

    for obj_id, states in data['objects'].items():
        for state in states[:10]:  # Check first 10 states
            for key in state.keys():
                if key.startswith('Agent.'):
                    has_cam = True
                    cam_keys.add(key)

    if has_cam:
        print("  ✓ CAM metadata detected")
        print(f"  Found {len(cam_keys)} unique Agent.* keys:")
        for key in sorted(cam_keys)[:10]:
            print(f"    - {key}")
        if len(cam_keys) > 10:
            print(f"    ... and {len(cam_keys) - 10} more")
    else:
        print("  ✗ No CAM metadata found (standard ACMI)")


def cmd_validate(args):
    """Validate ACMI file format."""
    print(f"Validating ACMI file: {args.input}")

    try:
        parser = ACMIParser()
        data = parser.parse_file(args.input)

        print("\n✓ File format is valid")
        print(f"  Objects: {len(data['objects'])}")
        print(f"  Events: {len(data['events'])}")

        # Check for common issues
        warnings = []

        # Check for empty objects
        for obj_id, states in data['objects'].items():
            if len(states) == 0:
                warnings.append(f"Object {obj_id} has no states")

        # Check for missing critical properties
        for obj_id, states in data['objects'].items():
            if states and 'Latitude' not in states[0]:
                warnings.append(f"Object {obj_id} missing position data")

        if warnings:
            print("\nWarning: Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("\n✓ No issues detected")

    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        sys.exit(1)


def cmd_convert(args):
    """Convert ACMI to FlightEpisode and back (roundtrip test)."""
    print(f"Testing roundtrip conversion: {args.input}")

    # Import
    converter = ACMIConverter()
    episodes = converter.acmi_to_episodes(args.input)

    print(f"  Loaded {len(episodes)} episode(s)")

    # Export back
    temp_output = Path(args.input).with_suffix('.roundtrip.txt.acmi')
    if len(episodes) > 0:
        converter.episode_to_acmi(episodes[0], str(temp_output))
        print(f"  Exported to: {temp_output}")

    print("\n✓ Roundtrip conversion successful")

    if args.keep:
        print(f"  Kept roundtrip file: {temp_output}")
    else:
        temp_output.unlink()
        print("  Removed temporary file")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TensorBoard Flight Plugin - ACMI Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import single ACMI file
  python -m tensorboard_flight.acmi import mission.txt.acmi --output runs/imported

  # Batch import directory
  python -m tensorboard_flight.acmi batch-import acmi_files/ --output runs/all

  # Show file information
  python -m tensorboard_flight.acmi info mission.txt.acmi

  # Validate ACMI format
  python -m tensorboard_flight.acmi validate mission.txt.acmi

  # Test roundtrip conversion
  python -m tensorboard_flight.acmi convert mission.txt.acmi
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import ACMI file to TensorBoard')
    import_parser.add_argument('input', help='Input ACMI file (.txt.acmi)')
    import_parser.add_argument('--output', '-o', default='runs/imported',
                              help='Output TensorBoard directory (default: runs/imported)')
    import_parser.add_argument('--prefix', '-p', default='acmi',
                              help='Agent ID prefix (default: acmi)')
    import_parser.set_defaults(func=cmd_import)

    # Batch import command
    batch_parser = subparsers.add_parser('batch-import', help='Batch import ACMI files')
    batch_parser.add_argument('input_dir', help='Input directory containing ACMI files')
    batch_parser.add_argument('--output', '-o', default='runs/imported',
                             help='Output TensorBoard directory (default: runs/imported)')
    batch_parser.add_argument('--pattern', '-p', default='*.txt.acmi',
                             help='File pattern (default: *.txt.acmi)')
    batch_parser.set_defaults(func=cmd_batch_import)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export TensorBoard episode to ACMI')
    export_parser.add_argument('--logdir', required=True, help='TensorBoard log directory')
    export_parser.add_argument('--output', '-o', required=True, help='Output ACMI file')
    export_parser.add_argument('--episode', help='Episode ID to export')
    export_parser.set_defaults(func=cmd_export)

    # Info command
    info_parser = subparsers.add_parser('info', help='Display ACMI file information')
    info_parser.add_argument('input', help='Input ACMI file')
    info_parser.set_defaults(func=cmd_info)

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate ACMI file format')
    validate_parser.add_argument('input', help='Input ACMI file')
    validate_parser.set_defaults(func=cmd_validate)

    # Convert (roundtrip test) command
    convert_parser = subparsers.add_parser('convert', help='Test roundtrip conversion')
    convert_parser.add_argument('input', help='Input ACMI file')
    convert_parser.add_argument('--keep', action='store_true',
                               help='Keep roundtrip output file')
    convert_parser.set_defaults(func=cmd_convert)

    # Parse args
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run command
    args.func(args)


if __name__ == '__main__':
    main()
