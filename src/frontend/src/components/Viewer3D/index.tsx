/**
 * 3D Viewer component using Three.js
 */

import React, { useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Grid, Sky } from '@react-three/drei';
import { useFlightStore } from '../../store';
import { FlightDataPoint } from '../../types';
import Aircraft from './Aircraft';
import TrajectoryTrail from './TrajectoryTrail';
import './Viewer3D.css';

// Helper to interpolate angles with proper wrapping around 360°/0° boundary
function interpolateAngle(a0: number, a1: number, alpha: number): number {
  // Compute the shortest angular distance
  let diff = a1 - a0;

  // Wrap difference to [-180, 180]
  while (diff > 180) diff -= 360;
  while (diff < -180) diff += 360;

  return a0 + alpha * diff;
}

// Helper to interpolate between data points
function interpolateDataPoint(
  points: FlightDataPoint[],
  time: number
): FlightDataPoint | null {
  if (points.length === 0) return null;
  if (time <= points[0].timestamp) return points[0];
  if (time >= points[points.length - 1].timestamp) return points[points.length - 1];

  // Binary search for the right interval
  let left = 0;
  let right = points.length - 1;

  while (right - left > 1) {
    const mid = Math.floor((left + right) / 2);
    if (points[mid].timestamp <= time) {
      left = mid;
    } else {
      right = mid;
    }
  }

  const p0 = points[left];
  const p1 = points[right];
  const alpha = (time - p0.timestamp) / (p1.timestamp - p0.timestamp);

  // Linear interpolation for position and velocity
  return {
    ...p0,
    timestamp: time,
    position: [
      p0.position[0] + alpha * (p1.position[0] - p0.position[0]),
      p0.position[1] + alpha * (p1.position[1] - p0.position[1]),
      p0.position[2] + alpha * (p1.position[2] - p0.position[2]),
    ],
    // Use wrapped interpolation for Euler angles to handle 0°/360° boundary
    orientation: {
      roll: interpolateAngle(p0.orientation.roll, p1.orientation.roll, alpha),
      pitch: interpolateAngle(p0.orientation.pitch, p1.orientation.pitch, alpha),
      yaw: interpolateAngle(p0.orientation.yaw, p1.orientation.yaw, alpha),
    },
    velocity: [
      p0.velocity[0] + alpha * (p1.velocity[0] - p0.velocity[0]),
      p0.velocity[1] + alpha * (p1.velocity[1] - p0.velocity[1]),
      p0.velocity[2] + alpha * (p1.velocity[2] - p0.velocity[2]),
    ],
  };
}

const Scene: React.FC = () => {
  const selectedEpisode = useFlightStore((state) => state.selectedEpisode);
  const currentTime = useFlightStore((state) => state.currentTime);
  const isPlaying = useFlightStore((state) => state.isPlaying);
  const playbackSpeed = useFlightStore((state) => state.playbackSpeed);
  const setCurrentTime = useFlightStore((state) => state.setCurrentTime);
  const setIsPlaying = useFlightStore((state) => state.setIsPlaying);
  const showTrail = useFlightStore((state) => state.showTrail);
  const trailLength = useFlightStore((state) => state.trailLength);
  const trailColorMode = useFlightStore((state) => state.trailColorMode);
  const cameraLocked = useFlightStore((state) => state.cameraLocked);

  // Update time on each frame when playing
  useFrame((state, delta) => {
    if (isPlaying && selectedEpisode) {
      const newTime = currentTime + delta * playbackSpeed;
      const maxTime = selectedEpisode.trajectory[selectedEpisode.trajectory.length - 1].timestamp;

      if (newTime >= maxTime) {
        setIsPlaying(false);
        setCurrentTime(maxTime);
      } else {
        setCurrentTime(newTime);
      }
    }
  });

  const currentDataPoint = useMemo(() => {
    if (!selectedEpisode) return null;
    return interpolateDataPoint(selectedEpisode.trajectory, currentTime);
  }, [selectedEpisode, currentTime]);

  if (!selectedEpisode || !currentDataPoint) {
    return null;
  }

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <directionalLight position={[-10, -10, -5]} intensity={0.3} />

      {/* Sky */}
      <Sky sunPosition={[100, 20, 100]} />

      {/* Ground grid */}
      <Grid
        args={[1000, 1000]}
        cellSize={10}
        cellThickness={0.5}
        cellColor="#6b6b6b"
        sectionSize={100}
        sectionThickness={1}
        sectionColor="#9d4b4b"
        fadeDistance={500}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={true}
      />

      {/* Aircraft */}
      <Aircraft dataPoint={currentDataPoint} />

      {/* Trajectory trail */}
      {showTrail && (
        <TrajectoryTrail
          trajectory={selectedEpisode.trajectory}
          currentTime={currentTime}
          length={trailLength}
          colorMode={trailColorMode}
        />
      )}

      {/* Camera controls */}
      <Controls dataPoint={currentDataPoint} />
    </>
  );
};

const Controls: React.FC<{ dataPoint: FlightDataPoint | null }> = ({ dataPoint }) => {
  const cameraLocked = useFlightStore((state) => state.cameraLocked);
  const controlsRef = useRef<any>(null);

  // Update the target when camera is locked
  useFrame(() => {
    if (cameraLocked && dataPoint && controlsRef.current) {
      // Convert position from NED to Three.js Y-up (same as in Aircraft.tsx)
      const aircraftX = dataPoint.position[1];     // NED.East → Three.X (Right)
      const aircraftY = -dataPoint.position[2];    // -NED.Down → Three.Y (Up)
      const aircraftZ = -dataPoint.position[0];    // -NED.North → Three.Z (Forward)

      // Smoothly move the orbit target to the aircraft
      controlsRef.current.target.lerp(
        { x: aircraftX, y: aircraftY, z: aircraftZ },
        0.1
      );
      controlsRef.current.update();
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.05}
      minDistance={5}
      maxDistance={500}
    />
  );
};

const Viewer3D: React.FC = () => {
  return (
    <div className="viewer3d">
      <Canvas
        camera={{
          position: [50, 30, 50],
          fov: 60,
          near: 0.1,
          far: 10000,
        }}
      >
        <Scene />
      </Canvas>
    </div>
  );
};

export default Viewer3D;
