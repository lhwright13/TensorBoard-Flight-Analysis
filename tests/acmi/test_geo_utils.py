"""Tests for geodetic coordinate conversion utilities."""

import unittest
import math
from tensorboard_flight.acmi.geo_utils import (
    geodetic_to_cartesian,
    cartesian_to_geodetic,
    compute_velocity_from_airspeed,
    compute_airspeed_from_velocity,
    normalize_longitude,
    normalize_heading,
    validate_geodetic,
)


class TestGeoConversion(unittest.TestCase):
    """Test coordinate conversions."""

    def test_geodetic_to_cartesian_origin(self):
        """Test conversion at origin."""
        # At reference point, should be (0, 0, 0)
        ref = (34.9054, -117.8839, 700.0)
        x, y, z = geodetic_to_cartesian(34.9054, -117.8839, 700.0, ref)

        self.assertAlmostEqual(x, 0.0, places=1)
        self.assertAlmostEqual(y, 0.0, places=1)
        self.assertAlmostEqual(z, 0.0, places=1)

    def test_geodetic_to_cartesian_north(self):
        """Test conversion North of origin."""
        ref = (34.9054, -117.8839, 700.0)
        # 0.01 degrees ≈ 1.11 km north
        x, y, z = geodetic_to_cartesian(34.9154, -117.8839, 700.0, ref)

        self.assertAlmostEqual(x, 0.0, places=0)
        self.assertGreater(y, 1000.0)  # > 1 km
        self.assertAlmostEqual(z, 0.0, places=1)

    def test_geodetic_to_cartesian_east(self):
        """Test conversion East of origin."""
        ref = (34.9054, -117.8839, 700.0)
        # 0.01 degrees ≈ 0.9 km east
        x, y, z = geodetic_to_cartesian(34.9054, -117.8739, 700.0, ref)

        self.assertGreater(x, 800.0)  # > 800m
        self.assertAlmostEqual(y, 0.0, places=0)
        self.assertAlmostEqual(z, 0.0, places=1)

    def test_cartesian_to_geodetic_roundtrip(self):
        """Test roundtrip conversion."""
        ref = (34.9054, -117.8839, 700.0)

        # Original geodetic
        lat1, lon1, alt1 = 34.92, -117.87, 1000.0

        # Convert to Cartesian and back
        x, y, z = geodetic_to_cartesian(lat1, lon1, alt1, ref)
        lat2, lon2, alt2 = cartesian_to_geodetic((x, y, z), ref)

        self.assertAlmostEqual(lat1, lat2, places=5)
        self.assertAlmostEqual(lon1, lon2, places=5)
        self.assertAlmostEqual(alt1, alt2, places=1)

    def test_compute_velocity_from_airspeed_level(self):
        """Test velocity computation for level flight."""
        # Level flight (0 pitch), heading North (0 yaw)
        airspeed = 50.0
        pitch = 0.0
        yaw = 0.0

        vx, vy, vz = compute_velocity_from_airspeed(airspeed, pitch, yaw)

        self.assertAlmostEqual(vx, 0.0, places=1)
        self.assertAlmostEqual(vy, 50.0, places=1)
        self.assertAlmostEqual(vz, 0.0, places=1)

    def test_compute_velocity_from_airspeed_climbing(self):
        """Test velocity computation for climbing flight."""
        # 10° climb, heading East (90°)
        airspeed = 50.0
        pitch = 10.0
        yaw = 90.0

        vx, vy, vz = compute_velocity_from_airspeed(airspeed, pitch, yaw)

        # Should have East, small North, and vertical components
        self.assertGreater(vx, 45.0)  # Mostly East
        self.assertAlmostEqual(vy, 0.0, places=0)
        self.assertGreater(vz, 5.0)  # Some vertical

    def test_compute_airspeed_from_velocity_roundtrip(self):
        """Test roundtrip airspeed calculation."""
        # Original
        airspeed1 = 60.0
        pitch1 = 15.0
        yaw1 = 45.0

        # Compute velocity
        velocity = compute_velocity_from_airspeed(airspeed1, pitch1, yaw1)

        # Convert back
        airspeed2, pitch2, yaw2 = compute_airspeed_from_velocity(velocity)

        self.assertAlmostEqual(airspeed1, airspeed2, places=1)
        self.assertAlmostEqual(pitch1, pitch2, places=1)
        self.assertAlmostEqual(yaw1, yaw2, places=1)


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_normalize_longitude(self):
        """Test longitude normalization."""
        self.assertAlmostEqual(normalize_longitude(0), 0)
        self.assertAlmostEqual(normalize_longitude(180), 180)
        self.assertAlmostEqual(normalize_longitude(181), -179)
        self.assertAlmostEqual(normalize_longitude(-181), 179)
        self.assertAlmostEqual(normalize_longitude(360), 0)
        self.assertAlmostEqual(normalize_longitude(720), 0)

    def test_normalize_heading(self):
        """Test heading normalization."""
        self.assertAlmostEqual(normalize_heading(0), 0)
        self.assertAlmostEqual(normalize_heading(180), 180)
        self.assertAlmostEqual(normalize_heading(360), 0)
        self.assertAlmostEqual(normalize_heading(450), 90)
        self.assertAlmostEqual(normalize_heading(-90), 270)

    def test_validate_geodetic_valid(self):
        """Test validation of valid coordinates."""
        self.assertTrue(validate_geodetic(34.9, -117.9, 1000))
        self.assertTrue(validate_geodetic(0, 0, 0))
        self.assertTrue(validate_geodetic(90, 180, 10000))
        self.assertTrue(validate_geodetic(-90, -180, 0))

    def test_validate_geodetic_invalid(self):
        """Test validation of invalid coordinates."""
        self.assertFalse(validate_geodetic(91, 0, 0))   # Lat > 90
        self.assertFalse(validate_geodetic(-91, 0, 0))  # Lat < -90
        self.assertFalse(validate_geodetic(0, 181, 0))  # Lon > 180
        self.assertFalse(validate_geodetic(0, -181, 0)) # Lon < -180
        self.assertFalse(validate_geodetic(0, 0, 200000))  # Alt too high


if __name__ == '__main__':
    unittest.main()
