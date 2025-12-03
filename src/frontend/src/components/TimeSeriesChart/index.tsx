/**
 * Time series chart component using D3 for telemetry visualization
 */

import React, { useRef, useEffect, useMemo, useState } from 'react';
import * as d3 from 'd3';
import { useFlightStore } from '../../store';
import { FlightDataPoint } from '../../types';
import './TimeSeriesChart.css';

type MetricKey =
  | 'altitude'
  | 'airspeed'
  | 'vertical_speed'
  | 'g_force'
  | 'roll'
  | 'pitch'
  | 'reward'
  | 'cumulative_reward';

interface MetricConfig {
  label: string;
  unit: string;
  color: string;
  getValue: (p: FlightDataPoint) => number;
  domain?: [number, number];
}

const metricConfigs: Record<MetricKey, MetricConfig> = {
  altitude: {
    label: 'Altitude',
    unit: 'm',
    color: '#3b82f6',
    getValue: (p) => p.telemetry.altitude,
  },
  airspeed: {
    label: 'Airspeed',
    unit: 'm/s',
    color: '#10b981',
    getValue: (p) => p.telemetry.airspeed,
  },
  vertical_speed: {
    label: 'Vertical Speed',
    unit: 'm/s',
    color: '#8b5cf6',
    getValue: (p) => p.telemetry.vertical_speed,
  },
  g_force: {
    label: 'G-Force',
    unit: 'g',
    color: '#f59e0b',
    getValue: (p) => p.telemetry.g_force,
  },
  roll: {
    label: 'Roll',
    unit: '°',
    color: '#ef4444',
    getValue: (p) => p.orientation.roll,
  },
  pitch: {
    label: 'Pitch',
    unit: '°',
    color: '#06b6d4',
    getValue: (p) => p.orientation.pitch,
  },
  reward: {
    label: 'Reward',
    unit: '',
    color: '#22c55e',
    getValue: (p) => p.rl_metrics.reward,
  },
  cumulative_reward: {
    label: 'Cumulative Reward',
    unit: '',
    color: '#a855f7',
    getValue: (p) => p.rl_metrics.cumulative_reward,
  },
};

const defaultMetrics: MetricKey[] = ['altitude', 'airspeed', 'reward'];

const TimeSeriesChart: React.FC = () => {
  const svgContainerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const selectedEpisode = useFlightStore((state) => state.selectedEpisode);
  const currentTime = useFlightStore((state) => state.currentTime);
  const setCurrentTime = useFlightStore((state) => state.setCurrentTime);

  const [selectedMetrics, setSelectedMetrics] = useState<MetricKey[]>(defaultMetrics);
  const [dimensions, setDimensions] = useState({ width: 600, height: 120 });

  // Observe SVG container size - both width and height
  useEffect(() => {
    if (!svgContainerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({
            width: Math.max(width, 200),
            height: Math.max(height, 80)
          });
        }
      }
    });

    resizeObserver.observe(svgContainerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!selectedEpisode) return null;

    const trajectory = selectedEpisode.trajectory;
    const timeExtent = d3.extent(trajectory, (d) => d.timestamp) as [number, number];

    const series = selectedMetrics.map((key) => {
      const config = metricConfigs[key];
      const values = trajectory.map((p) => ({
        time: p.timestamp,
        value: config.getValue(p),
      }));
      const valueExtent = d3.extent(values, (d) => d.value) as [number, number];

      return {
        key,
        config,
        values,
        valueExtent,
      };
    });

    return { timeExtent, series };
  }, [selectedEpisode, selectedMetrics]);

  // Render chart with D3
  useEffect(() => {
    if (!svgRef.current || !chartData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 60, bottom: 30, left: 50 };
    const width = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    const g = svg
      .attr('width', dimensions.width)
      .attr('height', dimensions.height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Time scale (x-axis)
    const xScale = d3
      .scaleLinear()
      .domain(chartData.timeExtent)
      .range([0, width]);

    // Draw each series
    chartData.series.forEach((series, i) => {
      // Y scale for this series with 10% padding on each side
      const [yMin, yMax] = series.valueExtent;
      const yPadding = (yMax - yMin) * 0.1 || 1;
      const yScale = d3
        .scaleLinear()
        .domain([yMin - yPadding, yMax + yPadding])
        .nice()
        .range([chartHeight, 0]);

      // Line generator
      const line = d3
        .line<{ time: number; value: number }>()
        .x((d) => xScale(d.time))
        .y((d) => yScale(d.value))
        .curve(d3.curveMonotoneX);

      // Draw the line
      g.append('path')
        .datum(series.values)
        .attr('class', 'chart-line')
        .attr('fill', 'none')
        .attr('stroke', series.config.color)
        .attr('stroke-width', 1.5)
        .attr('d', line);

      // Add Y axis on right side for each series (stacked)
      if (i === 0) {
        // Primary Y axis on left
        const yAxis = d3.axisLeft(yScale).ticks(5);
        g.append('g')
          .attr('class', 'y-axis')
          .call(yAxis)
          .selectAll('text')
          .style('fill', series.config.color);

        g.append('text')
          .attr('class', 'axis-label')
          .attr('transform', 'rotate(-90)')
          .attr('y', -35)
          .attr('x', -chartHeight / 2)
          .attr('text-anchor', 'middle')
          .style('fill', series.config.color)
          .style('font-size', '10px')
          .text(`${series.config.label} (${series.config.unit})`);
      }
    });

    // X axis
    const xAxis = d3.axisBottom(xScale).ticks(10).tickFormat((d) => `${d}s`);
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${chartHeight})`)
      .call(xAxis);

    // Playhead line
    const playhead = g
      .append('line')
      .attr('class', 'playhead')
      .attr('y1', 0)
      .attr('y2', chartHeight)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4,2');

    // Update playhead position
    const updatePlayhead = (time: number) => {
      playhead.attr('x1', xScale(time)).attr('x2', xScale(time));
    };
    updatePlayhead(currentTime);

    // Click to seek
    const clickArea = g
      .append('rect')
      .attr('class', 'click-area')
      .attr('width', width)
      .attr('height', chartHeight)
      .attr('fill', 'transparent')
      .attr('cursor', 'pointer');

    clickArea.on('click', (event) => {
      const [x] = d3.pointer(event);
      const time = xScale.invert(x);
      const clampedTime = Math.max(
        chartData.timeExtent[0],
        Math.min(chartData.timeExtent[1], time)
      );
      setCurrentTime(clampedTime);
    });

    // Drag to scrub
    const drag = d3.drag<SVGRectElement, unknown>().on('drag', (event) => {
      const time = xScale.invert(event.x);
      const clampedTime = Math.max(
        chartData.timeExtent[0],
        Math.min(chartData.timeExtent[1], time)
      );
      setCurrentTime(clampedTime);
    });

    clickArea.call(drag);

  }, [chartData, dimensions, setCurrentTime]);

  // Update playhead on time change (without full re-render)
  useEffect(() => {
    if (!svgRef.current || !chartData) return;

    const margin = { top: 20, right: 60, bottom: 30, left: 50 };
    const width = dimensions.width - margin.left - margin.right;

    const xScale = d3
      .scaleLinear()
      .domain(chartData.timeExtent)
      .range([0, width]);

    d3.select(svgRef.current)
      .select('.playhead')
      .attr('x1', xScale(currentTime))
      .attr('x2', xScale(currentTime));
  }, [currentTime, chartData, dimensions]);

  const toggleMetric = (key: MetricKey) => {
    setSelectedMetrics((prev) => {
      if (prev.includes(key)) {
        return prev.filter((k) => k !== key);
      }
      return [...prev, key];
    });
  };

  if (!selectedEpisode) {
    return null;
  }

  return (
    <div className="time-series-chart">
      <div className="chart-header">
        <h4>Telemetry Charts</h4>
        <div className="metric-toggles">
          {(Object.keys(metricConfigs) as MetricKey[]).map((key) => (
            <button
              key={key}
              className={`metric-toggle ${selectedMetrics.includes(key) ? 'active' : ''}`}
              style={{
                borderColor: selectedMetrics.includes(key) ? metricConfigs[key].color : undefined,
                color: selectedMetrics.includes(key) ? metricConfigs[key].color : undefined,
              }}
              onClick={() => toggleMetric(key)}
            >
              {metricConfigs[key].label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-legend">
        {selectedMetrics.map((key) => (
          <div key={key} className="legend-item">
            <span
              className="legend-color"
              style={{ backgroundColor: metricConfigs[key].color }}
            />
            <span className="legend-label">
              {metricConfigs[key].label}
              {metricConfigs[key].unit && ` (${metricConfigs[key].unit})`}
            </span>
          </div>
        ))}
      </div>

      <div className="svg-container" ref={svgContainerRef}>
        <svg ref={svgRef} />
      </div>
    </div>
  );
};

export default TimeSeriesChart;
