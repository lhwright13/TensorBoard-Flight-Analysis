/**
 * Telemetry display panel component
 */

import React, { useMemo } from 'react';
import { useFlightStore } from '../../store';
import { FlightDataPoint } from '../../types';
import './TelemetryPanel.css';

// Helper to interpolate between data points
function interpolateDataPoint(
  points: FlightDataPoint[],
  time: number
): FlightDataPoint | null {
  if (points.length === 0) return null;
  if (time <= points[0].timestamp) return points[0];
  if (time >= points[points.length - 1].timestamp) return points[points.length - 1];

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

  return {
    ...p0,
    timestamp: time,
    telemetry: {
      ...p0.telemetry,
      airspeed: p0.telemetry.airspeed + alpha * (p1.telemetry.airspeed - p0.telemetry.airspeed),
      altitude: p0.telemetry.altitude + alpha * (p1.telemetry.altitude - p0.telemetry.altitude),
      vertical_speed: p0.telemetry.vertical_speed + alpha * (p1.telemetry.vertical_speed - p0.telemetry.vertical_speed),
    },
  };
}

const TelemetryPanel: React.FC = () => {
  const selectedEpisode = useFlightStore((state) => state.selectedEpisode);
  const currentTime = useFlightStore((state) => state.currentTime);

  const currentDataPoint = useMemo(() => {
    if (!selectedEpisode) return null;
    return interpolateDataPoint(selectedEpisode.trajectory, currentTime);
  }, [selectedEpisode, currentTime]);

  if (!selectedEpisode || !currentDataPoint) {
    return null;
  }

  const { telemetry, rl_metrics, orientation } = currentDataPoint;

  const formatValue = (value: number, decimals = 2): string => {
    return value.toFixed(decimals);
  };

  return (
    <div className="telemetry-panel">
      <h3>Telemetry</h3>

      {/* Flight State */}
      <div className="telemetry-section">
        <h4>Flight State</h4>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="label">Airspeed:</span>
            <span className="value">{formatValue(telemetry.airspeed)} m/s</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Altitude:</span>
            <span className="value">{formatValue(telemetry.altitude)} m</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Vertical Speed:</span>
            <span className="value">{formatValue(telemetry.vertical_speed, 1)} m/s</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Heading:</span>
            <span className="value">{formatValue(telemetry.heading, 0)}°</span>
          </div>
        </div>
      </div>

      {/* Orientation */}
      <div className="telemetry-section">
        <h4>Orientation</h4>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="label">Roll:</span>
            <span className="value">{formatValue(orientation.roll, 1)}°</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Pitch:</span>
            <span className="value">{formatValue(orientation.pitch, 1)}°</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Yaw:</span>
            <span className="value">{formatValue(orientation.yaw, 1)}°</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Bank Angle:</span>
            <span className="value">{formatValue(telemetry.bank_angle, 1)}°</span>
          </div>
        </div>
      </div>

      {/* Performance */}
      <div className="telemetry-section">
        <h4>Performance</h4>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="label">G-Force:</span>
            <span className="value">{formatValue(telemetry.g_force, 2)}g</span>
          </div>
          <div className="telemetry-item">
            <span className="label">AoA:</span>
            <span className="value">{formatValue(telemetry.aoa, 1)}°</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Turn Rate:</span>
            <span className="value">{formatValue(telemetry.turn_rate, 1)}°/s</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Throttle:</span>
            <span className="value">{formatValue(telemetry.throttle * 100, 0)}%</span>
          </div>
        </div>
      </div>

      {/* Controls */}
      {(telemetry.aileron !== undefined || telemetry.elevator !== undefined) && (
        <div className="telemetry-section">
          <h4>Control Surfaces</h4>
          <div className="telemetry-grid">
            {telemetry.aileron !== undefined && (
              <div className="telemetry-item">
                <span className="label">Aileron:</span>
                <span className="value">{formatValue(telemetry.aileron, 2)}</span>
              </div>
            )}
            {telemetry.elevator !== undefined && (
              <div className="telemetry-item">
                <span className="label">Elevator:</span>
                <span className="value">{formatValue(telemetry.elevator, 2)}</span>
              </div>
            )}
            {telemetry.rudder !== undefined && (
              <div className="telemetry-item">
                <span className="label">Rudder:</span>
                <span className="value">{formatValue(telemetry.rudder, 2)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* RL Metrics */}
      <div className="telemetry-section">
        <h4>RL Metrics</h4>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="label">Reward:</span>
            <span className={`value ${rl_metrics.reward >= 0 ? 'positive' : 'negative'}`}>
              {formatValue(rl_metrics.reward, 3)}
            </span>
          </div>
          <div className="telemetry-item">
            <span className="label">Cumulative:</span>
            <span className="value">{formatValue(rl_metrics.cumulative_reward, 2)}</span>
          </div>
          {rl_metrics.value_estimate !== undefined && (
            <div className="telemetry-item">
              <span className="label">Value:</span>
              <span className="value">{formatValue(rl_metrics.value_estimate, 2)}</span>
            </div>
          )}
          <div className="telemetry-item">
            <span className="label">Action:</span>
            <span className="value">
              [{rl_metrics.action.map((a) => a.toFixed(2)).join(', ')}]
            </span>
          </div>
        </div>
      </div>

      {/* Reward Components */}
      {rl_metrics.reward_components && (
        <div className="telemetry-section">
          <h4>Reward Components</h4>
          <div className="telemetry-grid">
            {Object.entries(rl_metrics.reward_components).map(([key, value]) => (
              <div key={key} className="telemetry-item">
                <span className="label">{key}:</span>
                <span className={`value ${value >= 0 ? 'positive' : 'negative'}`}>
                  {formatValue(value, 3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TelemetryPanel;
