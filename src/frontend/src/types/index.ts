/**
 * Type definitions for flight data structures.
 */

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Orientation {
  roll: number;   // degrees
  pitch: number;  // degrees
  yaw: number;    // degrees
}

export interface Telemetry {
  airspeed: number;
  altitude: number;
  g_force: number;
  throttle: number;
  aoa: number;
  aos: number;
  heading: number;
  vertical_speed: number;
  turn_rate: number;
  bank_angle: number;
  aileron?: number;
  elevator?: number;
  rudder?: number;
}

export interface RLMetrics {
  reward: number;
  cumulative_reward: number;
  action: number[];
  policy_logprob?: number;
  value_estimate?: number;
  advantage?: number;
  entropy?: number;
  reward_components?: Record<string, number>;
}

export interface Event {
  timestamp: number;
  event_type: string;
  severity: string;
  message: string;
  metadata?: Record<string, any>;
}

export interface FlightDataPoint {
  timestamp: number;
  step: number;
  position: number[];  // [x, y, z]
  orientation: Orientation;
  velocity: number[];  // [vx, vy, vz]
  angular_velocity: number[];  // [p, q, r]
  telemetry: Telemetry;
  rl_metrics: RLMetrics;
  events?: Event[];
}

export interface FlightEpisode {
  episode_id: string;
  agent_id: string;
  episode_number: number;
  start_time: number;
  duration: number;
  total_steps: number;
  total_reward: number;
  success: boolean;
  termination_reason: string;
  trajectory: FlightDataPoint[];
  config?: Record<string, any>;
  tags?: string[];
}

export interface Run {
  run: string;
  tags: string[];
}

export interface EpisodeMetadata {
  step: number;
  wall_time: number;
}

export type CameraMode = 'free' | 'external' | 'cockpit' | 'satellite';
export type TrailColorMode = 'speed' | 'altitude' | 'reward';
