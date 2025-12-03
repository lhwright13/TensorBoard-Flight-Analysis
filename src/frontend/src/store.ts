/**
 * Global state management using Zustand.
 */

import { create } from 'zustand';
import { FlightEpisode, CameraMode, TrailColorMode } from './types';

interface FlightState {
  // Data
  selectedRun: string | null;
  selectedEpisode: FlightEpisode | null;

  // Playback state
  currentTime: number;
  isPlaying: boolean;
  playbackSpeed: number;

  // Visualization settings
  cameraMode: CameraMode;
  cameraLocked: boolean;
  showTrail: boolean;
  trailLength: number;
  trailColorMode: TrailColorMode;

  // Actions
  setSelectedRun: (run: string | null) => void;
  setSelectedEpisode: (episode: FlightEpisode | null) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
  setCameraMode: (mode: CameraMode) => void;
  setCameraLocked: (locked: boolean) => void;
  setShowTrail: (show: boolean) => void;
  setTrailLength: (length: number) => void;
  setTrailColorMode: (mode: TrailColorMode) => void;
}

export const useFlightStore = create<FlightState>((set) => ({
  // Initial state
  selectedRun: null,
  selectedEpisode: null,
  currentTime: 0,
  isPlaying: false,
  playbackSpeed: 1.0,
  cameraMode: 'external',
  cameraLocked: false,
  showTrail: true,
  trailLength: 100,
  trailColorMode: 'speed',

  // Actions
  setSelectedRun: (run) => set({ selectedRun: run }),
  setSelectedEpisode: (episode) => set({
    selectedEpisode: episode,
    currentTime: 0,
    isPlaying: false,
  }),
  setCurrentTime: (time) => set({ currentTime: time }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackSpeed: (speed) => set({ playbackSpeed: speed }),
  setCameraMode: (mode) => set({ cameraMode: mode }),
  setCameraLocked: (locked) => set({ cameraLocked: locked }),
  setShowTrail: (show) => set({ showTrail: show }),
  setTrailLength: (length) => set({ trailLength: length }),
  setTrailColorMode: (mode) => set({ trailColorMode: mode }),
}));
