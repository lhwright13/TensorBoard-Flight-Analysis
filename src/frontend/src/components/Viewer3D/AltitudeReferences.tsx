/**
 * Altitude Reference Planes
 *
 * Displays horizontal semi-transparent planes at key altitudes to improve
 * 3D spatial awareness. Essential for analyzing altitude control performance.
 */

import React from 'react';
import { Plane } from '@react-three/drei';
import * as THREE from 'three';

interface AltitudeReferencesProps {
  altitudes?: number[];  // Altitudes in meters (default: [0, 50, 100, 200])
  size?: number;         // Size of reference planes (default: 500m)
  opacity?: number;      // Opacity of planes (default: 0.15)
  visible?: boolean;     // Toggle visibility
}

const DEFAULT_ALTITUDES = [0, 50, 100, 200];

// Color palette for different altitudes
const ALTITUDE_COLORS: { [key: number]: string } = {
  0: '#ff4444',    // Red for ground level (danger)
  50: '#ffaa44',   // Orange for low altitude
  100: '#44aaff',  // Blue for medium altitude
  200: '#44ff44',  // Green for high altitude
};

const AltitudeReferences: React.FC<AltitudeReferencesProps> = ({
  altitudes = DEFAULT_ALTITUDES,
  size = 500,
  opacity = 0.15,
  visible = true,
}) => {
  if (!visible) return null;

  return (
    <group>
      {altitudes.map((altitude) => {
        // Convert from meters to Three.js Y-up coordinate
        // In NED, altitude = -Z, so Y = altitude (already positive up)
        const y = altitude;
        const color = ALTITUDE_COLORS[altitude] || '#888888';

        return (
          <group key={altitude}>
            {/* Reference plane */}
            <Plane
              args={[size, size]}
              position={[0, y, 0]}
              rotation={[-Math.PI / 2, 0, 0]}
            >
              <meshBasicMaterial
                color={color}
                transparent
                opacity={opacity}
                side={THREE.DoubleSide}
                depthWrite={false}
              />
            </Plane>

            {/* Altitude label at corners */}
            <group position={[size / 2 - 20, y + 0.5, size / 2 - 20]}>
              <sprite scale={[10, 5, 1]}>
                <spriteMaterial
                  map={createTextTexture(`${altitude}m`, color)}
                  transparent
                  depthTest={false}
                />
              </sprite>
            </group>
          </group>
        );
      })}
    </group>
  );
};

// Helper to create text texture for labels
function createTextTexture(text: string, color: string): THREE.Texture {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d')!;
  canvas.width = 256;
  canvas.height = 128;

  // Draw background
  context.fillStyle = 'rgba(0, 0, 0, 0.7)';
  context.fillRect(0, 0, canvas.width, canvas.height);

  // Draw text
  context.fillStyle = color;
  context.font = 'bold 48px Arial';
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

export default AltitudeReferences;
