# TensorBoard Flight Plugin - Frontend

React + TypeScript frontend for 3D flight trajectory visualization.

## Features

- **3D Viewer**: Three.js-based interactive 3D visualization
  - Aircraft model with orientation
  - Trajectory trail with color-coded modes (speed, altitude, reward)
  - Orbit camera controls
  - Grid reference and sky

- **Timeline Controls**: Playback control interface
  - Play/pause playback
  - Adjustable speed (0.25x to 8x)
  - Scrubber for jumping to specific time
  - Event markers for crashes/checkpoints

- **Telemetry Panel**: Real-time flight data display
  - Flight state (airspeed, altitude, heading, etc.)
  - Orientation (roll, pitch, yaw)
  - Performance metrics (g-force, AoA, turn rate)
  - Control surfaces (aileron, elevator, rudder)
  - RL metrics (reward, value, action)
  - Reward component breakdown

## Setup

### Install Dependencies

```bash
cd src/frontend
npm install
```

### Build

```bash
npm run build
```

This compiles the TypeScript and bundles everything to `../../tensorboard_flight/static/index.js`.

### Development Mode

```bash
npm run dev
```

Watches for changes and rebuilds automatically.

## Project Structure

```
src/frontend/
├── package.json
├── tsconfig.json
├── webpack.config.js
└── src/
    ├── index.tsx           # Entry point
    ├── App.tsx             # Main app component
    ├── App.css             # Global styles
    ├── store.ts            # Zustand state management
    ├── types/
    │   └── index.ts        # TypeScript type definitions
    └── components/
        ├── Viewer3D/       # 3D visualization
        │   ├── index.tsx
        │   ├── Aircraft.tsx
        │   ├── TrajectoryTrail.tsx
        │   └── Viewer3D.css
        ├── Timeline/       # Playback controls
        │   ├── index.tsx
        │   └── Timeline.css
        └── TelemetryPanel/ # Flight data display
            ├── index.tsx
            └── TelemetryPanel.css
```

## Technologies

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Three.js**: 3D graphics
- **React Three Fiber**: React wrapper for Three.js
- **Drei**: Three.js helpers
- **Zustand**: State management
- **Webpack**: Module bundler

## State Management

Global state is managed using Zustand in `store.ts`:

- `selectedRun`: Current run selection
- `selectedEpisode`: Current episode data
- `currentTime`: Playback time position
- `isPlaying`: Playback state
- `playbackSpeed`: Playback speed multiplier
- `cameraMode`: Camera view mode
- `showTrail`: Toggle trajectory trail
- `trailLength`: Number of trail points
- `trailColorMode`: Trail coloring (speed/altitude/reward)

## Components

### Viewer3D

Main 3D visualization component with:
- Three.js scene setup
- Camera controls (OrbitControls)
- Aircraft rendering with real-time orientation
- Trajectory trail with color coding
- Grid and environment

### Timeline

Playback control interface with:
- Play/pause button
- Time scrubber with drag support
- Speed selection buttons
- Event markers
- Time display

### TelemetryPanel

Live flight data display organized into sections:
- Flight State
- Orientation
- Performance
- Control Surfaces
- RL Metrics
- Reward Components

All values update in real-time as playback progresses.

## Next Steps

To use this frontend with TensorBoard:
1. Build the frontend: `npm run build`
2. Run your training with FlightLogger
3. Start TensorBoard: `tensorboard --logdir runs/`
4. Navigate to the "Flight" tab

The plugin will automatically load the bundled JavaScript and render the visualization.
