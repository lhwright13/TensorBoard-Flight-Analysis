"""Tests for ACMI parser."""

import unittest
import tempfile
from pathlib import Path
from tensorboard_flight.acmi.parser import ACMIParser


class TestACMIParser(unittest.TestCase):
    """Test ACMI file parsing."""

    def setUp(self):
        """Create temp directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temp directory."""
        self.temp_dir.cleanup()

    def create_sample_acmi(self, filename='test.txt.acmi', with_cam=False):
        """Create a sample ACMI file for testing."""
        filepath = self.temp_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("FileType=text/acmi/tacview\n")
            f.write("FileVersion=2.2\n")
            f.write("\n")
            f.write("0,ReferenceTime=2025-10-23T00:00:00Z\n")
            f.write('0,Title="Test Flight"\n')
            f.write("\n")
            f.write("#0.0\n")
            f.write('a01,Type=Air+FixedWing,Name="TestAgent",Coalition=Blue\n')
            f.write("\n")
            f.write("#0.1\n")
            if with_cam:
                # Write state with CAM metadata on same line
                f.write("a01,T=-117.88|34.91|1000.0|0.0|5.0|90.0,IAS=50.0,Throttle=0.7")
                f.write(",Agent.Reward.Instant=1.5")
                f.write(",Agent.Action.0=0.1")
                f.write(",Agent.Action.1=0.2\n")
            else:
                f.write("a01,T=-117.88|34.91|1000.0|0.0|5.0|90.0,IAS=50.0,Throttle=0.7\n")

            f.write("#0.2\n")
            f.write("a01,T=-117.88|34.92|1010.0|0.5|5.1|90.5,IAS=51.0\n")
            f.write("\n")
            f.write("#1.0\n")
            f.write("-a01\n")

        return filepath

    def test_parse_header(self):
        """Test header parsing."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        self.assertEqual(data['global']['FileVersion'], '2.2')
        self.assertEqual(data['global']['ReferenceTime'], '2025-10-23T00:00:00Z')
        self.assertEqual(data['global']['Title'], 'Test Flight')

    def test_parse_objects(self):
        """Test object parsing."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        self.assertIn('a01', data['objects'])
        states = data['objects']['a01']
        self.assertEqual(len(states), 3)  # 3 updates

    def test_parse_transform(self):
        """Test transform parsing."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        states = data['objects']['a01']
        first_update = states[1]  # Second state has transform

        self.assertEqual(first_update['Longitude'], -117.88)
        self.assertEqual(first_update['Latitude'], 34.91)
        self.assertEqual(first_update['Altitude'], 1000.0)
        self.assertEqual(first_update['Roll'], 0.0)
        self.assertEqual(first_update['Pitch'], 5.0)
        self.assertEqual(first_update['Yaw'], 90.0)

    def test_parse_timestamps(self):
        """Test timestamp parsing."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        states = data['objects']['a01']
        self.assertEqual(states[0]['timestamp'], 0.0)
        self.assertEqual(states[1]['timestamp'], 0.1)
        self.assertEqual(states[2]['timestamp'], 0.2)

    def test_parse_with_cam(self):
        """Test parsing with CAM metadata."""
        filepath = self.create_sample_acmi(with_cam=True)

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        states = data['objects']['a01']
        cam_state = states[1]

        self.assertIn('Agent.Reward.Instant', cam_state)
        self.assertEqual(cam_state['Agent.Reward.Instant'], 1.5)
        self.assertEqual(cam_state['Agent.Action.0'], 0.1)
        self.assertEqual(cam_state['Agent.Action.1'], 0.2)

    def test_get_object_by_name(self):
        """Test finding object by name."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        result = parser.get_object_by_name("TestAgent")
        self.assertIsNotNone(result)
        obj_id, states = result
        self.assertEqual(obj_id, 'a01')
        self.assertGreater(len(states), 0)

    def test_get_all_object_names(self):
        """Test getting all object names."""
        filepath = self.create_sample_acmi()

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        names = parser.get_all_object_names()
        self.assertIn('a01', names)
        self.assertEqual(names['a01'], 'TestAgent')

    def test_parse_quoted_strings(self):
        """Test parsing quoted strings with special chars."""
        filepath = self.temp_path / 'test.txt.acmi'

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("FileType=text/acmi/tacview\n")
            f.write("FileVersion=2.2\n")
            f.write('\n')
            f.write('0,Title="Flight with, comma"\n')
            f.write('#0.0\n')
            f.write('a01,Name="Agent \\"Alpha\\""\n')

        parser = ACMIParser()
        data = parser.parse_file(str(filepath))

        self.assertEqual(data['global']['Title'], 'Flight with, comma')
        self.assertEqual(data['objects']['a01'][0]['Name'], 'Agent "Alpha"')


if __name__ == '__main__':
    unittest.main()
