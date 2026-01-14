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

import React, { useRef, Suspense, Component, ReactNode, useMemo } from 'react';
import { Euler, Vector3, Group, MeshStandardMaterial, Mesh } from 'three';
import { useGLTF } from '@react-three/drei';
import { FlightDataPoint } from '../../types';

// Aircraft material - applied to all meshes since GLB lost materials during optimization
const AIRCRAFT_MATERIAL = new MeshStandardMaterial({
  color: 0x4a5568,      // Gray color (like military aircraft)
  metalness: 0.6,
  roughness: 0.4,
});

// Model path - served from TensorBoard plugin static directory (optimized GLB)
const MODEL_PATH = '/data/plugin/flight/static/models/fighter_jet.glb';

// Scale factor for the aircraft model (adjust based on model's native size)
const MODEL_SCALE = 0.02;

interface AircraftProps {
  dataPoint: FlightDataPoint;
}

// Error boundary for catching model loading errors
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ModelErrorBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode; fallback: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Aircraft model loading error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Fallback aircraft - simple geometric shape when model fails to load
const FallbackAircraft: React.FC<{ position: [number, number, number]; rotation: Euler }> = ({
  position,
  rotation
}) => (
  <group position={position} rotation={rotation}>
    {/* Fuselage */}
    <mesh>
      <boxGeometry args={[4, 0.8, 0.8]} />
      <meshStandardMaterial color="#3b82f6" />
    </mesh>
    {/* Wings */}
    <mesh position={[0, 0, 0]}>
      <boxGeometry args={[0.5, 0.15, 5]} />
      <meshStandardMaterial color="#60a5fa" />
    </mesh>
    {/* Tail */}
    <mesh position={[-1.5, 0.5, 0]}>
      <boxGeometry args={[0.3, 1, 0.15]} />
      <meshStandardMaterial color="#60a5fa" />
    </mesh>
    {/* Nose */}
    <mesh position={[2.2, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
      <coneGeometry args={[0.4, 0.8, 8]} />
      <meshStandardMaterial color="#2563eb" />
    </mesh>
  </group>
);

// Loading fallback - wireframe shape while model loads
const LoadingFallback: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <mesh position={position}>
    <boxGeometry args={[2, 0.5, 0.5]} />
    <meshStandardMaterial color="#3b82f6" wireframe />
  </mesh>
);

// The fighter jet model component
const FighterJetModel: React.FC<{ position: [number, number, number]; rotation: Euler }> = ({
  position,
  rotation
}) => {
  const groupRef = useRef<Group>(null);
  const { scene } = useGLTF(MODEL_PATH);

  // Clone the scene and apply material to all meshes
  const clonedScene = useMemo(() => {
    const clone = scene.clone();
    // Apply material to all meshes (materials were lost during OBJ->GLB conversion)
    clone.traverse((child) => {
      if (child instanceof Mesh) {
        child.material = AIRCRAFT_MATERIAL;
      }
    });
    return clone;
  }, [scene]);

  return (
    <group position={position} rotation={rotation}>
      {/* Model orientation correction: adjust based on model's default orientation */}
      <group
        ref={groupRef}
        rotation={[-Math.PI / 2, 0, 0]}  // Rotate to align nose with +X axis
        scale={MODEL_SCALE}
      >
        <primitive object={clonedScene} />
      </group>
    </group>
  );
};

// Preload the model for better performance
useGLTF.preload(MODEL_PATH);

const Aircraft: React.FC<AircraftProps> = ({ dataPoint }) => {
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
      {/* Fighter Jet model with error boundary and loading fallback */}
      <ModelErrorBoundary fallback={<FallbackAircraft position={position} rotation={rotation} />}>
        <Suspense fallback={<LoadingFallback position={position} />}>
          <FighterJetModel position={position} rotation={rotation} />
        </Suspense>
      </ModelErrorBoundary>

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
