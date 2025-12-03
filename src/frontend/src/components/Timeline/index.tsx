/**
 * Timeline component for playback control
 */

import React, { useRef, useEffect, useState } from 'react';
import { useFlightStore } from '../../store';
import './Timeline.css';

const Timeline: React.FC = () => {
  const selectedEpisode = useFlightStore((state) => state.selectedEpisode);
  const currentTime = useFlightStore((state) => state.currentTime);
  const isPlaying = useFlightStore((state) => state.isPlaying);
  const playbackSpeed = useFlightStore((state) => state.playbackSpeed);
  const setCurrentTime = useFlightStore((state) => state.setCurrentTime);
  const setIsPlaying = useFlightStore((state) => state.setIsPlaying);
  const setPlaybackSpeed = useFlightStore((state) => state.setPlaybackSpeed);

  const [isDragging, setIsDragging] = useState(false);
  const timelineRef = useRef<HTMLDivElement>(null);

  if (!selectedEpisode) {
    return null;
  }

  const maxTime = selectedEpisode.trajectory[selectedEpisode.trajectory.length - 1].timestamp;
  const progress = (currentTime / maxTime) * 100;

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * maxTime;

    setCurrentTime(Math.max(0, Math.min(newTime, maxTime)));
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    handleTimelineClick(e);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(x / rect.width, 1));
    const newTime = percentage * maxTime;

    setCurrentTime(newTime);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);

      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, maxTime]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
  };

  const speeds = [0.25, 0.5, 1, 2, 4, 8];

  return (
    <div className="timeline">
      <div className="timeline-header">
        <h3>Playback Control</h3>
        <div className="episode-info">
          Episode {selectedEpisode.episode_number} | {selectedEpisode.total_steps} steps | Reward: {selectedEpisode.total_reward.toFixed(2)}
        </div>
      </div>

      <div className="timeline-controls">
        {/* Play/Pause button */}
        <button className="control-button play-pause" onClick={handlePlayPause}>
          {isPlaying ? '⏸' : '▶'}
        </button>

        {/* Time display */}
        <div className="time-display">
          {formatTime(currentTime)} / {formatTime(maxTime)}
        </div>

        {/* Speed controls */}
        <div className="speed-controls">
          <label>Speed:</label>
          {speeds.map((speed) => (
            <button
              key={speed}
              className={`speed-button ${playbackSpeed === speed ? 'active' : ''}`}
              onClick={() => handleSpeedChange(speed)}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Timeline scrubber */}
      <div
        ref={timelineRef}
        className="timeline-scrubber"
        onMouseDown={handleMouseDown}
        onClick={handleTimelineClick}
      >
        <div className="timeline-track">
          <div className="timeline-progress" style={{ width: `${progress}%` }} />
          <div className="timeline-handle" style={{ left: `${progress}%` }} />
        </div>

        {/* Event markers */}
        {selectedEpisode.trajectory.filter((p) => p.events && p.events.length > 0).map((point, idx) => {
          const pos = (point.timestamp / maxTime) * 100;
          return (
            <div
              key={idx}
              className="event-marker"
              style={{ left: `${pos}%` }}
              title={point.events?.[0].message}
            />
          );
        })}
      </div>
    </div>
  );
};

export default Timeline;
