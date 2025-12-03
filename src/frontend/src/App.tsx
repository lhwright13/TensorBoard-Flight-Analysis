/**
 * Main App component for TensorBoard Flight Plugin.
 */

import React, { useCallback } from 'react';
import { useFlightStore } from './store';
import Selector from './components/Selector';
import Viewer3D from './components/Viewer3D';
import Timeline from './components/Timeline';
import TelemetryPanel from './components/TelemetryPanel';
import TrailLegend from './components/TrailLegend';
import TimeSeriesChart from './components/TimeSeriesChart';
import './App.css';

const App: React.FC = () => {
  const selectedRun = useFlightStore((state) => state.selectedRun);
  const selectedEpisode = useFlightStore((state) => state.selectedEpisode);
  const cameraLocked = useFlightStore((state) => state.cameraLocked);
  const setCameraLocked = useFlightStore((state) => state.setCameraLocked);

  // Handle ACMI export download
  const handleExportACMI = useCallback(() => {
    if (!selectedRun || !selectedEpisode) {
      console.error('[Flight Plugin] Export ACMI: No run or episode selected');
      return;
    }

    // Construct the export URL - use absolute path for TensorBoard plugin
    const exportUrl = `/data/plugin/flight/export_acmi?run=${encodeURIComponent(selectedRun)}&episode_id=${encodeURIComponent(selectedEpisode.episode_id)}`;
    console.log('[Flight Plugin] Exporting ACMI:', exportUrl);

    // Try multiple download methods to handle sandboxed iframe restrictions
    try {
      // Method 1: Try top-level window navigation (works if same-origin)
      // Content-Disposition: attachment header will trigger download instead of navigation
      if (window.top && window.top !== window) {
        window.top.location.href = exportUrl;
        return;
      }
    } catch (e) {
      console.log('[Flight Plugin] Top-level navigation blocked, trying fallback');
    }

    // Method 2: Create anchor element with download attribute
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `${selectedEpisode.episode_id}.txt.acmi`;
    link.target = '_top'; // Try to open in top frame
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [selectedRun, selectedEpisode]);

  return (
    <div className="app-container">
      {/* Run/Episode Selector */}
      <Selector />

      {!selectedEpisode ? (
        <div className="empty-state">
          <h2>No Flight Data Loaded</h2>
          <p>Select a run and episode above to view the flight trajectory.</p>
        </div>
      ) : (
        <>
          <div className="viewer-container">
            <Viewer3D />

            {/* Camera lock toggle and export button */}
            <div className="camera-controls">
              <button
                className={`camera-lock-btn ${cameraLocked ? 'active' : ''}`}
                onClick={() => setCameraLocked(!cameraLocked)}
                title={cameraLocked ? 'Unlock camera' : 'Lock camera to aircraft'}
              >
                {cameraLocked ? 'Camera Locked' : 'Free Camera'}
              </button>
              <button
                className="export-acmi-btn"
                onClick={handleExportACMI}
                title="Download episode as ACMI file (Tacview format)"
              >
                Export ACMI
              </button>
            </div>

            {/* Trail legend and controls */}
            <TrailLegend />
          </div>

          <div className="bottom-panel">
            <div className="charts-section">
              <div className="timeline-container">
                <Timeline />
              </div>
              <div className="chart-container">
                <TimeSeriesChart />
              </div>
            </div>

            <div className="telemetry-container">
              <TelemetryPanel />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default App;
