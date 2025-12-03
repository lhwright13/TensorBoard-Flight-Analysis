/**
 * Trajectory trail visualization component
 */

import React, { useMemo } from 'react';
import { Line } from '@react-three/drei';
import { FlightDataPoint, TrailColorMode } from '../../types';
import * as THREE from 'three';

interface TrajectoryTrailProps {
  trajectory: FlightDataPoint[];
  currentTime: number;
  length: number;  // Number of past points to show
  colorMode: TrailColorMode;
}

function getColorForDataPoint(point: FlightDataPoint, mode: TrailColorMode): THREE.Color {
  switch (mode) {
    case 'speed': {
      const speed = Math.sqrt(
        point.velocity[0] ** 2 + point.velocity[1] ** 2 + point.velocity[2] ** 2
      );
      // Map speed (0-50 m/s) to color (blue to red)
      const t = Math.min(speed / 50, 1);
      return new THREE.Color().setHSL(0.6 - t * 0.6, 1, 0.5);
    }

    case 'altitude': {
      // Map altitude (0-200m) to color (blue to green)
      const alt = point.telemetry.altitude;
      const t = Math.min(alt / 200, 1);
      return new THREE.Color().setHSL(0.6 - t * 0.3, 1, 0.5);
    }

    case 'reward': {
      // Map reward (-1 to 1) to color (red to green)
      const reward = point.rl_metrics.reward;
      const t = (reward + 1) / 2;  // Normalize to 0-1
      return new THREE.Color().setHSL(t * 0.3, 1, 0.5);
    }

    default:
      return new THREE.Color(0x00ff00);
  }
}

const TrajectoryTrail: React.FC<TrajectoryTrailProps> = ({
  trajectory,
  currentTime,
  length,
  colorMode,
}) => {
  const trailData = useMemo(() => {
    // Find current index
    let currentIndex = trajectory.findIndex((p) => p.timestamp > currentTime);
    if (currentIndex === -1) currentIndex = trajectory.length;

    // Get past points
    const startIndex = Math.max(0, currentIndex - length);
    const points = trajectory.slice(startIndex, currentIndex);

    if (points.length < 2) return null;

    // Convert positions from NED to Three.js Y-up coordinate system
    // (Same transformation as in Aircraft.tsx)
    const positions: THREE.Vector3[] = points.map(
      (p) => new THREE.Vector3(
        p.position[1],     // NED.East → Three.X (Right)
        -p.position[2],    // -NED.Down → Three.Y (Up)
        -p.position[0]     // -NED.North → Three.Z (Forward)
      )
    );

    // Get colors
    const colors: THREE.Color[] = points.map((p) => getColorForDataPoint(p, colorMode));

    return { positions, colors };
  }, [trajectory, currentTime, length, colorMode]);

  if (!trailData) return null;

  return (
    <Line
      points={trailData.positions}
      color="white"  // Will be overridden by vertex colors
      vertexColors={trailData.colors}
      lineWidth={2}
    />
  );
};

export default TrajectoryTrail;
