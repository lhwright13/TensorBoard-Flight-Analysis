# Testing the TensorBoard Flight Plugin

This document covers testing both the backend (Phase 1) and frontend (Phase 2) of the plugin.

---

# Frontend Testing (Phase 2)

## Quick Start

1. **Generate test data** (if not already done):
   ```bash
   cd tensorboard_flight_plugin
   ../venv/bin/python generate_test_episode.py
   ```

2. **Start the test server**:
   ```bash
   cd src/frontend
   python3 serve_test.py
   ```

3. **Open in browser**:
   Navigate to http://localhost:8080/test.html

## What You Should See

The test page displays a complete 3D flight visualization:

- **3D Viewer** (center): Interactive 3D visualization showing:
  - Aircraft model following a circular flight path
  - Trajectory trail behind the aircraft
  - Grid reference and sky dome
  - Orbit camera controls (click and drag to rotate, scroll to zoom)

- **Timeline Controls** (bottom): Playback interface with:
  - Play/pause button
  - Time scrubber (drag to jump to any point)
  - Speed controls (0.25x, 0.5x, 1x, 2x, 4x, 8x)
  - Current time display

- **Telemetry Panel** (right): Live flight data showing:
  - Flight State (airspeed, altitude, heading, vertical speed)
  - Orientation (roll, pitch, yaw, bank angle)
  - Performance (g-force, angle of attack, turn rate, throttle)
  - Control Surfaces (aileron, elevator, rudder)
  - RL Metrics (reward, cumulative reward, value, action)
  - Reward Components breakdown

## Generating Custom Test Data

Create a new test episode with custom parameters:

```bash
cd tensorboard_flight_plugin
../venv/bin/python generate_test_episode.py
```

The script generates a circular flight pattern with:
- 300 timesteps (30 seconds at 10 Hz)
- Circular path with 100m radius
- Altitude variation between 45-55m
- Banking turns and pitch variations
- Realistic telemetry and RL metrics

## Extracting Real Flight Data

If you have logged flight data from training:

```bash
cd tensorboard_flight_plugin
../venv/bin/python extract_test_data.py path/to/tensorboard/logs
```

This extracts the first episode and writes it to `src/frontend/test-data.js`.

## Building the Frontend

After making changes to the frontend code:

```bash
cd src/frontend
npm run build
```

This compiles TypeScript and bundles to `../../tensorboard_flight/static/index.js`.

For development with auto-rebuild:

```bash
npm run dev
```

## Troubleshooting Frontend

**"Failed to load application bundle" error:**
- Run `npm run build` in `src/frontend/`
- Check that `tensorboard_flight/static/index.js` exists

**"Loading flight data..." never goes away:**
- Check browser console for errors
- Verify `test-data.js` exists and is valid JSON
- Access via HTTP (not file://)

**3D view is blank:**
- Open browser console for WebGL errors
- Try Chrome or Firefox
- Check GPU supports WebGL

**Console errors about React:**
- Verify internet connection (React loads from CDN)
- Check React CDN scripts load correctly

---

# Backend Testing (Phase 1)

## Quick Test (5 minutes)

Test the basic FlightLogger with your RateControlEnv:

```bash
cd /Users/lhwri/controls

# Install the plugin
pip install -e tensorboard_flight_plugin/

# Run quick test with random policy
./venv/bin/python test_flight_logger.py
```

This will:
- Create a RateControlEnv environment
- Run 3 short episodes with random actions
- Log all flight data (position, orientation, velocity, telemetry, RL metrics)
- Save to `learned_controllers/logs/flight_test/`

**Expected output:**
```
Testing FlightLogger with RateControlEnv
Creating FlightLogger at: learned_controllers/logs/flight_test
Creating RateControlEnv...

Running 3 test episodes...

  Episode 1/3
    Step 50, reward=...
    Step 100, reward=...
    Logged 250 steps

  Episode 2/3
    ...

TEST COMPLETE!
Logged 3 episodes to: learned_controllers/logs/flight_test
```

## View Logged Data

Start TensorBoard:

```bash
tensorboard --logdir learned_controllers/logs/flight_test
```

Open http://localhost:6006

**What you'll see:**
- TensorBoard loads the data
- Events are stored in protobuf format
- "Flight" tab will appear (once frontend is built in Phase 2)
- For now, data is logged correctly but visualization pending

## Integration with Training

Use the FlightLogger during actual RL training:

```bash
# Run training with flight logging enabled
./venv/bin/python learned_controllers/train_rate_with_flight_viz.py \
  --config learned_controllers/config/quick_test.yaml \
  --flight-viz

# This will create TWO TensorBoard log directories:
# 1. learned_controllers/logs/tensorboard - Standard SB3 metrics
# 2. learned_controllers/logs/tensorboard_flight - Flight trajectories
```

**Features:**
- Automatically logs every 10th episode (configurable)
- Captures full flight trajectory with:
  - Position, orientation, velocity
  - Telemetry (airspeed, altitude, g-force, etc.)
  - RL metrics (reward, action, value, policy logprob)
  - Reward components breakdown
  - Events (crashes, terminations)
- Minimal overhead (~1-2% slowdown)

## Advanced: Full Training with Logging

Run a full training session with flight visualization:

```bash
./venv/bin/python learned_controllers/train_rate_with_flight_viz.py \
  --config learned_controllers/config/ppo_lstm.yaml \
  --flight-viz
```

During training:
- Flight trajectories logged every 10 episodes
- View standard metrics: `tensorboard --logdir learned_controllers/logs/tensorboard`
- View flight data: `tensorboard --logdir learned_controllers/logs/tensorboard_flight`

## What Data is Logged

For each episode, the FlightLogger captures:

**Per-Step Data:**
- **Kinematic State:**
  - Position: [x, y, z] in meters
  - Orientation: [roll, pitch, yaw] in degrees
  - Velocity: [vx, vy, vz] in m/s
  - Angular rates: [p, q, r] in rad/s

- **Telemetry:**
  - Airspeed, altitude, g-force
  - Control surfaces (aileron, elevator, rudder, throttle)
  - Heading, vertical speed, turn rate
  - Bank angle, AoA, AoS

- **RL Metrics:**
  - Reward (step and cumulative)
  - Action vector
  - Value estimate (if available)
  - Policy log probability
  - Reward components (tracking, smoothness, stability, etc.)

**Episode Metadata:**
- Episode ID, agent ID, episode number
- Total reward, success flag
- Duration, number of steps
- Termination reason
- Tags for filtering

## File Structure

After running tests:

```
learned_controllers/logs/
├── flight_test/                 # Quick test output
│   └── events.out.tfevents.*   # TensorBoard event file with flight data
└── tensorboard_flight/          # Training output
    └── events.out.tfevents.*
```

## Troubleshooting

### Import Error: "No module named 'tensorboard_flight'"
```bash
cd /Users/lhwri/controls
pip install -e tensorboard_flight_plugin/
```

### No flight data appearing
Check that:
1. FlightLogger was created: `logger = FlightLogger(log_dir=...)`
2. Episodes were logged: `logger.start_episode()` → `logger.log_flight_data()` → `logger.end_episode()`
3. Logger was closed: `logger.close()`
4. Event files exist in the log directory

### TensorBoard not showing data
- The 3D visualization frontend (Phase 2) is not yet built
- Data is correctly logged in event files
- You can verify with: `ls -lh learned_controllers/logs/flight_test/`

## Next Steps

Phase 2 will add:
- 3D visualization frontend (Three.js)
- Interactive trajectory viewer
- Telemetry panels
- Playback controls

For now, Phase 1 successfully logs all flight data to TensorBoard format!

## Verification

To verify Phase 1 is working:

1. Run test: `./venv/bin/python test_flight_logger.py`
2. Check files created: `ls -lh learned_controllers/logs/flight_test/`
3. Start TensorBoard: `tensorboard --logdir learned_controllers/logs/flight_test`
4. Verify no errors in TensorBoard startup
5. Check event file contains data: Should be >1KB per episode

**Success criteria:**
- No import errors
- FlightLogger creates event files
- Episode data is serialized to protobuf
- TensorBoard loads without errors
- Frontend visualization complete and working

---

# Project Files

```
tensorboard_flight_plugin/
├── generate_test_episode.py    # Generate synthetic test data
├── extract_test_data.py        # Extract data from TensorBoard logs
├── test_flight_logger.py       # Backend integration test
├── TESTING.md                  # This file
├── src/
│   ├── tensorboard_flight/     # Python backend
│   │   ├── logger.py           # FlightLogger API
│   │   ├── plugin.py           # TensorBoard plugin
│   │   └── data/schema.py      # Data structures
│   └── frontend/
│       ├── test.html           # Standalone test page
│       ├── test-data.js        # Test flight data (generated)
│       ├── serve_test.py       # HTTP server for testing
│       └── src/                # React/TypeScript source
│           ├── index.tsx       # Entry point
│           ├── App.tsx         # Main app
│           ├── store.ts        # State management
│           └── components/     # UI components
└── tests/                      # Unit tests
    ├── test_schema.py
    └── test_logger.py
```

## Next Steps

**Phase 3** - Full TensorBoard Integration:
1. Complete the plugin backend REST API
2. Integrate frontend with TensorBoard's iframe system
3. Add multi-episode comparison view
4. Add episode filtering and search
5. Implement camera modes (follow, chase, cockpit)
6. Add trajectory export functionality
