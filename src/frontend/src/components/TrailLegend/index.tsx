/**
 * Trail color legend and controls component
 */

import React from 'react';
import { useFlightStore } from '../../store';
import { TrailColorMode } from '../../types';
import './TrailLegend.css';

interface ColorStop {
  color: string;
  label: string;
}

const colorModeConfig: Record<TrailColorMode, { name: string; unit: string; stops: ColorStop[] }> = {
  speed: {
    name: 'Speed',
    unit: 'm/s',
    stops: [
      { color: 'hsl(216, 100%, 50%)', label: '0' },
      { color: 'hsl(108, 100%, 50%)', label: '25' },
      { color: 'hsl(0, 100%, 50%)', label: '50+' },
    ],
  },
  altitude: {
    name: 'Altitude',
    unit: 'm',
    stops: [
      { color: 'hsl(216, 100%, 50%)', label: '0' },
      { color: 'hsl(162, 100%, 50%)', label: '100' },
      { color: 'hsl(108, 100%, 50%)', label: '200+' },
    ],
  },
  reward: {
    name: 'Reward',
    unit: '',
    stops: [
      { color: 'hsl(0, 100%, 50%)', label: '-1' },
      { color: 'hsl(54, 100%, 50%)', label: '0' },
      { color: 'hsl(108, 100%, 50%)', label: '+1' },
    ],
  },
};

const TrailLegend: React.FC = () => {
  const showTrail = useFlightStore((state) => state.showTrail);
  const setShowTrail = useFlightStore((state) => state.setShowTrail);
  const trailColorMode = useFlightStore((state) => state.trailColorMode);
  const setTrailColorMode = useFlightStore((state) => state.setTrailColorMode);
  const trailLength = useFlightStore((state) => state.trailLength);
  const setTrailLength = useFlightStore((state) => state.setTrailLength);

  const config = colorModeConfig[trailColorMode];

  const gradientColors = config.stops.map((s) => s.color).join(', ');

  return (
    <div className="trail-legend">
      <div className="trail-controls">
        <label className="trail-toggle">
          <input
            type="checkbox"
            checked={showTrail}
            onChange={(e) => setShowTrail(e.target.checked)}
          />
          <span>Show Trail</span>
        </label>

        {showTrail && (
          <>
            <div className="color-mode-selector">
              <label>Color by:</label>
              <div className="mode-buttons">
                {(Object.keys(colorModeConfig) as TrailColorMode[]).map((mode) => (
                  <button
                    key={mode}
                    className={`mode-btn ${trailColorMode === mode ? 'active' : ''}`}
                    onClick={() => setTrailColorMode(mode)}
                  >
                    {colorModeConfig[mode].name}
                  </button>
                ))}
              </div>
            </div>

            <div className="trail-length-control">
              <label>Trail Length: {trailLength}</label>
              <input
                type="range"
                min="10"
                max="500"
                value={trailLength}
                onChange={(e) => setTrailLength(parseInt(e.target.value, 10))}
              />
            </div>
          </>
        )}
      </div>

      {showTrail && (
        <div className="legend-display">
          <div className="legend-title">
            {config.name} {config.unit && `(${config.unit})`}
          </div>
          <div className="legend-bar">
            <div
              className="gradient-bar"
              style={{ background: `linear-gradient(to right, ${gradientColors})` }}
            />
            <div className="legend-labels">
              {config.stops.map((stop, i) => (
                <span key={i} className="legend-label">
                  {stop.label}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrailLegend;
