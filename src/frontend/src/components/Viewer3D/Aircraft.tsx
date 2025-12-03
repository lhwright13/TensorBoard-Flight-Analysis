/**
 * Aircraft 3D model component
 *
 * COORDINATE SYSTEM TRANSFORMATIONS:
 *
 * Source (Simulation): NED (North-East-Down)
 *   - X: North (meters)
 *   - Y: East (meters)
 *   - Z: Down (meters, positive downward)
 *   - Attitude: Roll-Pitch-Yaw (degrees)
 *     - Roll: Right wing down is positive
 *     - Pitch: Nose up is positive
 *     - Yaw: 0° = North, 90° = East (clockwise positive)
 *
 * Target (Three.js): Right-handed Y-up
 *   - X: Right (meters)
 *   - Y: Up (meters, positive upward)
 *   - Z: Forward (meters, toward viewer)
 *
 * Transformation:
 *   Three.X = NED.East
 *   Three.Y = -NED.Down  (negate to flip vertical axis)
 *   Three.Z = -NED.North (negate for camera orientation)
 */

import React, { useRef } from 'react';
import { Mesh, Euler, Vector3 } from 'three';
import { FlightDataPoint } from '../../types';

interface AircraftProps {
  dataPoint: FlightDataPoint;
}

const Aircraft: React.FC<AircraftProps> = ({ dataPoint }) => {
  const meshRef = useRef<Mesh>(null);

  // Convert position from NED to Three.js Y-up coordinate system
  const position: [number, number, number] = [
    dataPoint.position[1],     // NED.East → Three.X (Right)
    -dataPoint.position[2],    // -NED.Down → Three.Y (Up)
    -dataPoint.position[0],    // -NED.North → Three.Z (Forward)
  ];

  // Convert orientation from NED to Three.js Y-up coordinate system
  // Euler angles in degrees → radians
  // Add -90° offset to yaw to align aircraft model (nose along +X) with NED convention
  const yawRad = ((dataPoint.orientation.yaw - 90) * Math.PI) / 180;
  const pitchRad = (dataPoint.orientation.pitch * Math.PI) / 180;
  const rollRad = (dataPoint.orientation.roll * Math.PI) / 180;

  // Apply aerospace-standard ZYX rotation sequence with correct sign conventions
  // for NED → Three.js Y-up transformation
  const rotation = new Euler(
    pitchRad,    // X-axis rotation: pitch (nose up is positive)
    -yawRad,     // Y-axis rotation: yaw (negated for Z-down to Y-up)
    -rollRad,    // Z-axis rotation: roll (negated for right-hand rule)
    'ZYX'        // Standard aerospace rotation sequence
  );

  // Velocity vector in world coordinates (Three.js Y-up)
  const velocityDir = new Vector3(
    dataPoint.velocity[1],     // NED.East → Three.X (Right)
    -dataPoint.velocity[2],    // -NED.Down → Three.Y (Up)
    -dataPoint.velocity[0]     // -NED.North → Three.Z (Forward)
  ).normalize();

  return (
    <>
      {/* Aircraft model - rotated to match orientation */}
      <group position={position} rotation={rotation}>
        {/* Simple aircraft representation - replace with actual 3D model */}

        {/* Fuselage */}
        <mesh ref={meshRef}>
          <boxGeometry args={[2, 0.5, 0.5]} />
          <meshStandardMaterial color="#3b82f6" />
        </mesh>

        {/* Wings */}
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[0.3, 0.1, 3]} />
          <meshStandardMaterial color="#60a5fa" />
        </mesh>

        {/* Tail */}
        <mesh position={[-0.8, 0.3, 0]}>
          <boxGeometry args={[0.2, 0.6, 0.1]} />
          <meshStandardMaterial color="#60a5fa" />
        </mesh>

        {/* Nose cone */}
        <mesh position={[1.1, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <coneGeometry args={[0.25, 0.5, 8]} />
          <meshStandardMaterial color="#2563eb" />
        </mesh>
      </group>

      {/* Velocity vector indicator - in world coordinates, NOT rotated with aircraft */}
      <arrowHelper
        args={[
          velocityDir,
          new Vector3(position[0], position[1], position[2]),
          3,
          0x00ff00,
          0.5,
          0.3,
        ]}
      />
    </>
  );
};

export default Aircraft;
