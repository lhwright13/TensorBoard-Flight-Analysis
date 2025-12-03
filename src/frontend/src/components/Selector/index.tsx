/**
 * Run and Episode selector component
 */

import React, { useEffect, useState } from 'react';
import { useFlightStore } from '../../store';
import { FlightEpisode } from '../../types';
import './Selector.css';

interface Run {
  run: string;
  tags: string[];
}

interface EpisodeMetadata {
  episode_id: string;
  agent_id: string;
  episode_number: number;
  total_steps: number;
  total_reward: number;
  success: boolean;
  duration: number;
  step: number;
  wall_time: number;
}

const Selector: React.FC = () => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [episodes, setEpisodes] = useState<EpisodeMetadata[]>([]);
  const [selectedRun, setSelectedRunLocal] = useState<string>('');
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const setSelectedEpisode = useFlightStore((state) => state.setSelectedEpisode);
  const setSelectedRun = useFlightStore((state) => state.setSelectedRun);

  // Fetch available runs
  useEffect(() => {
    fetch('/data/plugin/flight/runs')
      .then(res => res.json())
      .then(data => {
        if (data.runs && data.runs.length > 0) {
          setRuns(data.runs);
          setSelectedRunLocal(data.runs[0].run);
          setSelectedRun(data.runs[0].run);
        }
      })
      .catch(err => console.error('Error fetching runs:', err));
  }, [setSelectedRun]);

  // Fetch episodes when run changes
  useEffect(() => {
    if (!selectedRun) return;

    setLoading(true);
    fetch(`/data/plugin/flight/episodes?run=${encodeURIComponent(selectedRun)}`)
      .then(res => res.json())
      .then(data => {
        if (data.episodes && data.episodes.length > 0) {
          setEpisodes(data.episodes);
          setSelectedEpisodeId(data.episodes[0].episode_id);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching episodes:', err);
        setLoading(false);
      });
  }, [selectedRun]);

  // Load episode data when selection changes
  useEffect(() => {
    if (!selectedRun || !selectedEpisodeId) return;

    setLoading(true);
    fetch(`/data/plugin/flight/episode_data?run=${encodeURIComponent(selectedRun)}&episode_id=${encodeURIComponent(selectedEpisodeId)}`)
      .then(res => res.json())
      .then((episode: FlightEpisode) => {
        setSelectedEpisode(episode);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading episode:', err);
        setLoading(false);
      });
  }, [selectedRun, selectedEpisodeId, setSelectedEpisode]);

  return (
    <div className="selector-panel">
      <div className="selector-group">
        <label htmlFor="run-select">Run:</label>
        <select
          id="run-select"
          value={selectedRun}
          onChange={(e) => {
            setSelectedRunLocal(e.target.value);
            setSelectedRun(e.target.value);
          }}
          disabled={loading}
        >
          {runs.map(run => (
            <option key={run.run} value={run.run}>
              {run.run}
            </option>
          ))}
        </select>
      </div>

      <div className="selector-group">
        <label htmlFor="episode-select">Episode:</label>
        <select
          id="episode-select"
          value={selectedEpisodeId}
          onChange={(e) => setSelectedEpisodeId(e.target.value)}
          disabled={loading || episodes.length === 0}
        >
          {episodes.map(ep => (
            <option key={ep.episode_id} value={ep.episode_id}>
              {ep.episode_id} (R: {ep.total_reward.toFixed(1)}, Steps: {ep.total_steps})
            </option>
          ))}
        </select>
      </div>

      {loading && <div className="selector-loading">Loading...</div>}
    </div>
  );
};

export default Selector;
