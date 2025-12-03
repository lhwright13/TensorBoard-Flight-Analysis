# Changelog

All notable changes to the TensorBoard Flight Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 3: Telemetry Charts & Trail Enhancements
- **Time Series Charts** - D3-powered telemetry visualization:
  - Multi-metric display (altitude, airspeed, vertical speed, g-force, roll, pitch, reward, cumulative reward)
  - Toggle individual metrics on/off with color-coded legend
  - Interactive playhead synced with timeline
  - Click/drag to scrub through time
  - Responsive sizing to container
- **Trail Legend & Controls** - Enhanced trajectory visualization:
  - Toggle trail visibility
  - Color mode selector (Speed, Altitude, Reward)
  - Adjustable trail length (10-500 points)
  - Color gradient legend with units
  - Speed: Blue (0 m/s) to Red (50+ m/s)
  - Altitude: Blue (0m) to Green (200+ m)
  - Reward: Red (-1) to Green (+1)

### Planned
- Multi-agent comparison views
- Training evolution visualization
- Policy comparison tools
- PyPI package publication

## [0.1.0] - 2025-11-18

### Added - Phase 1: Foundation
- **FlightLogger API** - Core logging infrastructure for flight trajectories
- **Data Schemas** - Comprehensive data models (FlightDataPoint, FlightEpisode, Orientation, Telemetry, RLMetrics)
- **Protocol Buffers** - Efficient data serialization for TensorBoard
- **Stable-Baselines3 Integration** - FlightLoggerCallback for automatic logging during training
- **ACMI Support** - Full bidirectional import/export for Tacview compatibility
  - ACMILogger - Drop-in FlightLogger replacement with automatic ACMI export
  - ACMIParser - Parse ACMI 2.2 text format files
  - ACMIWriter - Write ACMI files with Custom Agent Metadata (CAM)
  - ACMIConverter - Lossless bidirectional conversion between ACMI and FlightEpisode
  - CLI tools - Command-line interface for import/export/validation
  - CAM Schema - Custom metadata encoding for RL metrics (rewards, actions, values)
  - Geodetic utilities - Coordinate conversions for geographic positioning
- **Test Suite** - 8 comprehensive test modules covering core functionality
  - Schema validation tests
  - Logger functionality tests
  - ACMI parser tests
  - CAM encoding/decoding tests
  - Geodetic conversion tests
  - Roundtrip conversion tests

### Added - Phase 2: 3D Visualization
- **Frontend Infrastructure** - React + TypeScript + Three.js stack
- **3D Flight Viewer** - Interactive visualization with:
  - Aircraft model with realistic orientation
  - Trajectory trail rendering
  - Grid reference and sky dome
  - Orbit camera controls (rotate, pan, zoom)
  - Multiple camera modes
- **Telemetry Panel** - Real-time display of:
  - Flight state (airspeed, altitude, heading, vertical speed)
  - Orientation (roll, pitch, yaw, bank angle)
  - Performance metrics (g-force, angle of attack, turn rate, throttle)
  - Control surfaces (aileron, elevator, rudder)
  - RL metrics (reward, cumulative reward, value, action)
  - Reward components breakdown
- **Timeline Controls** - Playback interface with:
  - Play/pause functionality
  - Time scrubber for jumping to any point
  - Speed controls (0.25x, 0.5x, 1x, 2x, 4x, 8x)
  - Current time display
- **TensorBoard Plugin** - Full integration with TensorBoard backend
  - Plugin registration and discovery
  - REST API endpoints for runs, episodes, and data
  - Static file serving for frontend assets

### Documentation
- README.md - Comprehensive overview and quick start guide
- DESIGN_PLAN.md - System architecture and implementation roadmap
- ACMI_SUPPORT.md - Complete ACMI integration guide
- TESTING.md - Frontend and backend testing instructions
- examples/ - Working code examples for basic usage and ACMI integration

### Infrastructure
- setup.py - Python package configuration
- webpack.config.js - Frontend build configuration
- tsconfig.json - TypeScript configuration
- requirements.txt - Python dependencies
- package.json - Node.js dependencies

## [0.0.1] - 2025-10-17

### Added
- Initial project structure
- Design documentation
- Development planning

---

## Version History

- **0.1.0** (2025-11-18) - Phase 1 & 2 Complete: Core infrastructure and 3D visualization
- **0.0.1** (2025-10-17) - Initial design and planning

## Upgrade Notes

### Upgrading to 0.1.0

This is the first functional release. No upgrade path needed.

## Breaking Changes

None yet. First release.

## Credits

- **Lucas Wright** ([@lhwright13](https://github.com/lhwright13)) - Main author
- Inspired by Tacview for professional flight analysis
- Built on TensorBoard plugin architecture
- Uses Three.js for 3D rendering
