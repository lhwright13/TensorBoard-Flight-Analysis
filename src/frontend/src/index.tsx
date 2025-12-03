/**
 * Entry point for TensorBoard Flight Plugin frontend.
 */

import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import { useFlightStore } from './store';
import { FlightEpisode } from './types';

// TensorBoard plugin entry point
export function render(element: HTMLElement) {
  ReactDOM.render(<App />, element);
}

// Load episode data (for testing)
export function loadEpisode(episode: FlightEpisode) {
  useFlightStore.getState().setSelectedEpisode(episode);
}

// Export to global scope for TensorBoard
(window as any).tensorboard_flight = {
  render,
  loadEpisode,
};

// For development/standalone testing
if (process.env.NODE_ENV === 'development') {
  const root = document.getElementById('root');
  if (root) {
    render(root);
  }
}
