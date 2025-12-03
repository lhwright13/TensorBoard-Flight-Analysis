"""Geodetic coordinate conversion utilities for ACMI format.

This module provides conversions between:
- Geodetic coordinates (latitude, longitude, altitude) used by ACMI
- Cartesian coordinates (x, y, z) used by the Flight Plugin

Uses a simple flat-earth approximation suitable for small areas (< 100km).
For larger areas, consider using pyproj library for accurate WGS84 transformations.
"""

import math
from typing import Tuple, Optional
import numpy as np


# Earth radius in meters (mean radius)
EARTH_RADIUS = 6371000.0

# Default reference point (Edwards AFB, CA)
DEFAULT_REF_LAT = 34.9054
DEFAULT_REF_LON = -117.8839
DEFAULT_REF_ALT = 700.0  # meters MSL


def geodetic_to_cartesian(
    lat: float,
    lon: float,
    alt: float,
    ref_point: Optional[Tuple[float, float, float]] = None
) -> Tuple[float, float, float]:
    """Convert geodetic coordinates (lat/lon/alt) to local Cartesian (x/y/z).

    Uses East-North-Up (ENU) coordinate system with flat-earth approximation.

    Args:
        lat: Latitude in degrees (-90 to +90, positive = North)
        lon: Longitude in degrees (-180 to +180, positive = East)
        alt: Altitude in meters MSL
        ref_point: Reference point (lat, lon, alt) for origin.
                  If None, uses default Edwards AFB location.

    Returns:
        Tuple of (x, y, z) in meters:
            x: East (positive = East)
            y: North (positive = North)
            z: Up (altitude - reference altitude)

    Example:
        >>> lat, lon, alt = 34.91, -117.88, 1000.0
        >>> x, y, z = geodetic_to_cartesian(lat, lon, alt)
        >>> # x ≈ 500m East, y ≈ 500m North, z ≈ 300m Up
    """
    if ref_point is None:
        ref_lat, ref_lon, ref_alt = DEFAULT_REF_LAT, DEFAULT_REF_LON, DEFAULT_REF_ALT
    else:
        ref_lat, ref_lon, ref_alt = ref_point

    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)

    # Compute deltas
    dlat = lat_rad - ref_lat_rad
    dlon = lon_rad - ref_lon_rad

    # ENU coordinates (flat-earth approximation)
    x = EARTH_RADIUS * dlon * math.cos(ref_lat_rad)  # East
    y = EARTH_RADIUS * dlat                          # North
    z = alt - ref_alt                                # Up

    return (x, y, z)


def cartesian_to_geodetic(
    position: Tuple[float, float, float],
    ref_point: Optional[Tuple[float, float, float]] = None
) -> Tuple[float, float, float]:
    """Convert local Cartesian (x/y/z) to geodetic coordinates (lat/lon/alt).

    Inverse of geodetic_to_cartesian using flat-earth approximation.

    Args:
        position: Tuple of (x, y, z) in meters (ENU)
        ref_point: Reference point (lat, lon, alt) for origin.
                  If None, uses default Edwards AFB location.

    Returns:
        Tuple of (lat, lon, alt):
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt: Altitude in meters MSL

    Example:
        >>> x, y, z = 500.0, 500.0, 300.0
        >>> lat, lon, alt = cartesian_to_geodetic((x, y, z))
        >>> # lat ≈ 34.91°N, lon ≈ -117.88°E, alt ≈ 1000m
    """
    if ref_point is None:
        ref_lat, ref_lon, ref_alt = DEFAULT_REF_LAT, DEFAULT_REF_LON, DEFAULT_REF_ALT
    else:
        ref_lat, ref_lon, ref_alt = ref_point

    x, y, z = position

    # Convert reference to radians
    ref_lat_rad = math.radians(ref_lat)
    ref_lon_rad = math.radians(ref_lon)

    # Compute deltas in radians
    dlat = y / EARTH_RADIUS
    dlon = x / (EARTH_RADIUS * math.cos(ref_lat_rad))

    # Convert back to degrees
    lat = math.degrees(ref_lat_rad + dlat)
    lon = math.degrees(ref_lon_rad + dlon)
    alt = ref_alt + z

    return (lat, lon, alt)


def compute_velocity_from_airspeed(
    airspeed: float,
    pitch: float,
    yaw: float
) -> Tuple[float, float, float]:
    """Compute velocity vector from airspeed and orientation.

    Assumes velocity is aligned with the aircraft's heading (no wind).

    Args:
        airspeed: True airspeed in m/s
        pitch: Pitch angle in degrees (positive = nose up)
        yaw: Yaw angle in degrees (0 = North, 90 = East, clockwise)

    Returns:
        Tuple of (vx, vy, vz) in m/s:
            vx: East velocity
            vy: North velocity
            vz: Up velocity (vertical speed)

    Example:
        >>> airspeed = 50.0  # m/s
        >>> pitch = 10.0     # 10° nose up
        >>> yaw = 45.0       # Northeast heading
        >>> vx, vy, vz = compute_velocity_from_airspeed(airspeed, pitch, yaw)
        >>> # vx ≈ 35m/s East, vy ≈ 35m/s North, vz ≈ 9m/s Up
    """
    pitch_rad = math.radians(pitch)
    yaw_rad = math.radians(yaw)

    # Decompose airspeed into horizontal and vertical components
    horizontal_speed = airspeed * math.cos(pitch_rad)
    vertical_speed = airspeed * math.sin(pitch_rad)

    # Decompose horizontal speed into East/North
    vx = horizontal_speed * math.sin(yaw_rad)  # East
    vy = horizontal_speed * math.cos(yaw_rad)  # North
    vz = vertical_speed                        # Up

    return (vx, vy, vz)


def compute_airspeed_from_velocity(
    velocity: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    """Compute airspeed and orientation from velocity vector.

    Inverse of compute_velocity_from_airspeed (assumes no wind).

    Args:
        velocity: Tuple of (vx, vy, vz) in m/s

    Returns:
        Tuple of (airspeed, pitch, yaw):
            airspeed: True airspeed in m/s
            pitch: Pitch angle in degrees
            yaw: Yaw angle in degrees (0 = North, 90 = East)

    Example:
        >>> vx, vy, vz = 35.0, 35.0, 9.0
        >>> airspeed, pitch, yaw = compute_airspeed_from_velocity((vx, vy, vz))
        >>> # airspeed ≈ 50 m/s, pitch ≈ 10°, yaw ≈ 45°
    """
    vx, vy, vz = velocity

    # Compute airspeed (magnitude)
    airspeed = math.sqrt(vx**2 + vy**2 + vz**2)

    # Compute pitch (angle from horizontal)
    horizontal_speed = math.sqrt(vx**2 + vy**2)
    if airspeed > 0:
        pitch = math.degrees(math.atan2(vz, horizontal_speed))
    else:
        pitch = 0.0

    # Compute yaw (heading)
    if horizontal_speed > 0:
        yaw = math.degrees(math.atan2(vx, vy))  # Note: atan2(East, North)
        # Normalize to [0, 360)
        if yaw < 0:
            yaw += 360.0
    else:
        yaw = 0.0

    return (airspeed, pitch, yaw)


def compute_reference_point(positions: list) -> Tuple[float, float, float]:
    """Compute a suitable reference point from a list of Cartesian positions.

    Uses the centroid of the positions as the origin.

    Args:
        positions: List of (x, y, z) tuples in Cartesian coordinates

    Returns:
        Tuple of (lat, lon, alt) for the reference point

    Example:
        >>> positions = [(0, 0, 0), (100, 100, 100), (-100, -100, -100)]
        >>> ref = compute_reference_point(positions)
        >>> # ref ≈ centroid in geodetic
    """
    if not positions:
        return (DEFAULT_REF_LAT, DEFAULT_REF_LON, DEFAULT_REF_ALT)

    # Compute centroid in Cartesian space
    positions_array = np.array(positions)
    centroid = positions_array.mean(axis=0)

    # Use first position's altitude as reference (simple heuristic)
    ref_alt = positions[0][2] if positions else DEFAULT_REF_ALT

    # For simplicity, use default lat/lon (in production, could compute from data)
    return (DEFAULT_REF_LAT, DEFAULT_REF_LON, ref_alt)


def validate_geodetic(lat: float, lon: float, alt: float) -> bool:
    """Validate geodetic coordinates are within valid ranges.

    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        alt: Altitude in meters

    Returns:
        True if coordinates are valid, False otherwise
    """
    if not (-90.0 <= lat <= 90.0):
        return False
    if not (-180.0 <= lon <= 180.0):
        return False
    if not (-1000.0 <= alt <= 100000.0):  # Reasonable altitude range
        return False
    return True


def normalize_longitude(lon: float) -> float:
    """Normalize longitude to [-180, 180] range.

    Args:
        lon: Longitude in degrees

    Returns:
        Normalized longitude in [-180, 180]
    """
    while lon > 180.0:
        lon -= 360.0
    while lon < -180.0:
        lon += 360.0
    return lon


def normalize_heading(heading: float) -> float:
    """Normalize heading to [0, 360) range.

    Args:
        heading: Heading in degrees

    Returns:
        Normalized heading in [0, 360)
    """
    heading = heading % 360.0
    if heading < 0:
        heading += 360.0
    return heading
