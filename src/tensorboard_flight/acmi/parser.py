"""ACMI file parser with CAM support.

This module parses ACMI 2.2 text format files, including Custom Agent Metadata (CAM)
extensions for RL/AI data.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class ACMIParser:
    """Parser for ACMI 2.2 text format with CAM support.

    Parses ACMI files line-by-line, extracting:
    - Global properties (reference time, title, author, etc.)
    - Object data (position, orientation, telemetry)
    - CAM metadata (RL metrics, control surfaces, etc.)
    - Events (bookmarks, messages, crashes, etc.)

    Example:
        >>> parser = ACMIParser()
        >>> data = parser.parse_file("mission.txt.acmi")
        >>> print(f"Found {len(data['objects'])} objects")
        >>> for obj_id, states in data['objects'].items():
        ...     print(f"Object {obj_id}: {len(states)} timesteps")
    """

    def __init__(self):
        """Initialize ACMI parser."""
        self.current_time = 0.0
        self.global_properties = {}
        self.objects = {}  # obj_id -> list of states
        self.events = []

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """Parse ACMI file and return structured data.

        Args:
            filepath: Path to .txt.acmi file

        Returns:
            Dictionary with:
                - 'global': Global properties dict
                - 'objects': Dict mapping object_id -> list of timestamped states
                - 'events': List of event dicts
                - 'reference_time': ISO timestamp string

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        self.current_time = 0.0
        self.global_properties = {}
        self.objects = {}
        self.events = []

        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"ACMI file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            # Read and validate header
            self._parse_header(f)

            # Parse remaining lines
            for line_num, line in enumerate(f, start=3):  # Start at 3 (after header)
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('//'):
                    continue

                try:
                    self._parse_line(line)
                except Exception as e:
                    # Continue parsing, but log error
                    print(f"Warning: Error parsing line {line_num}: {e}")
                    continue

        return {
            'global': self.global_properties,
            'objects': self.objects,
            'events': self.events,
            'reference_time': self.global_properties.get('ReferenceTime', None),
        }

    def _parse_header(self, f):
        """Parse and validate ACMI header.

        Args:
            f: File object

        Raises:
            ValueError: If header is invalid
        """
        line1 = f.readline().strip()
        line2 = f.readline().strip()

        if line1 != "FileType=text/acmi/tacview":
            raise ValueError(f"Invalid ACMI file: Expected FileType=text/acmi/tacview, got: {line1}")

        # Parse version
        if not line2.startswith("FileVersion="):
            raise ValueError(f"Invalid ACMI file: Expected FileVersion, got: {line2}")

        version = line2.split('=', 1)[1]
        self.global_properties['FileVersion'] = version

    def _parse_line(self, line: str):
        """Parse a single ACMI line.

        Args:
            line: Stripped line from ACMI file
        """
        # Time frame (e.g., #12.5)
        if line.startswith('#'):
            self.current_time = float(line[1:])
            return

        # Remove object (e.g., -3000102)
        if line.startswith('-'):
            obj_id = line[1:]
            # Could track removed objects if needed
            return

        # Object or global property update
        if ',' in line:
            # Split on first comma to separate ID from properties
            parts = line.split(',', 1)
            obj_id = parts[0].strip()
            props_str = parts[1] if len(parts) > 1 else ""

            # Parse properties
            props = self._parse_properties(props_str)
            props['timestamp'] = self.current_time

            # Object ID "0" is global metadata
            if obj_id == "0":
                self.global_properties.update(props)

                # Check for events
                if 'Event' in props:
                    event = self._parse_event(props['Event'], self.current_time)
                    self.events.append(event)
            else:
                # Regular object update
                if obj_id not in self.objects:
                    self.objects[obj_id] = []
                self.objects[obj_id].append(props)

    def _parse_properties(self, props_str: str) -> Dict[str, Any]:
        """Parse comma-separated key=value properties.

        Handles:
        - Escaped commas in quoted strings
        - Transform (T) special syntax
        - Type conversion (numbers, booleans, strings)

        Args:
            props_str: Comma-separated properties string

        Returns:
            Dictionary of property key -> value
        """
        props = {}

        # Split by comma, but preserve escaped commas in quotes
        parts = self._split_preserving_quotes(props_str)

        for part in parts:
            part = part.strip()
            if not part or '=' not in part:
                continue

            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Parse Transform (T) specially
            if key == 'T':
                transform = self._parse_transform(value)
                props.update(transform)
            else:
                # Parse value
                props[key] = self._parse_value(value)

        return props

    def _split_preserving_quotes(self, text: str) -> List[str]:
        """Split by comma, but preserve commas inside quoted strings.

        Args:
            text: Text to split

        Returns:
            List of parts
        """
        parts = []
        current = []
        in_quotes = False

        for char in text:
            if char == '"':
                in_quotes = not in_quotes
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)

        if current:
            parts.append(''.join(current))

        return parts

    def _parse_transform(self, t_str: str) -> Dict[str, Any]:
        """Parse Transform (T) property.

        Format: Lon|Lat|Alt or Lon|Lat|Alt|Roll|Pitch|Yaw or with U,V

        Args:
            t_str: Transform value string (pipe-separated)

        Returns:
            Dictionary with position, orientation, etc.
        """
        parts = [float(x) for x in t_str.split('|')]

        result = {}

        if len(parts) >= 3:
            lon, lat, alt = parts[0], parts[1], parts[2]
            result['Longitude'] = lon
            result['Latitude'] = lat
            result['Altitude'] = alt

        if len(parts) >= 6:
            roll, pitch, yaw = parts[3], parts[4], parts[5]
            result['Roll'] = roll
            result['Pitch'] = pitch
            result['Yaw'] = yaw

        if len(parts) >= 8:
            # U, V components (native coordinates)
            result['U'] = parts[6]
            result['V'] = parts[7]

        if len(parts) >= 9:
            # Heading (when using native coords)
            result['Heading'] = parts[8]

        return result

    def _parse_value(self, value: str) -> Any:
        """Parse a property value and convert to appropriate type.

        Args:
            value: Value string

        Returns:
            Converted value (int, float, bool, or str)
        """
        value = value.strip()

        # Boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False

        # Null
        if value.lower() == 'null':
            return None

        # Quoted string
        if value.startswith('"') and value.endswith('"'):
            # Remove quotes and unescape
            return value[1:-1].replace('\\"', '"').replace('\\,', ',')

        # Number (int or float)
        try:
            if '.' in value or 'e' in value.lower():
                return float(value)
            else:
                return int(value)
        except ValueError:
            # Return as string if can't parse
            return value

    def _parse_event(self, event_str: str, timestamp: float) -> Dict[str, Any]:
        """Parse Event property.

        Format: EventType|ObjectId|ObjectId|Message

        Args:
            event_str: Event value string
            timestamp: Current timestamp

        Returns:
            Event dictionary
        """
        parts = event_str.split('|')

        event = {
            'timestamp': timestamp,
            'type': parts[0] if len(parts) > 0 else 'Unknown',
        }

        # Parse additional fields based on event type
        if len(parts) > 1:
            # Could be object ID or message
            if parts[1].strip():
                event['target'] = parts[1]

        if len(parts) > 2 and parts[2].strip():
            event['message'] = parts[2]
        elif len(parts) > 1:
            # Single field might be a message
            event['message'] = parts[1]

        return event

    def get_object_by_name(self, name: str) -> Optional[Tuple[str, List[Dict]]]:
        """Find object by Name property.

        Args:
            name: Object name to search for

        Returns:
            Tuple of (object_id, states) or None if not found
        """
        for obj_id, states in self.objects.items():
            # Check first state for Name property
            if states and states[0].get('Name') == name:
                return (obj_id, states)
        return None

    def get_all_object_names(self) -> Dict[str, str]:
        """Get mapping of object IDs to names.

        Returns:
            Dictionary mapping object_id -> name
        """
        names = {}
        for obj_id, states in self.objects.items():
            if states:
                name = states[0].get('Name')
                if name:
                    names[obj_id] = name
        return names
