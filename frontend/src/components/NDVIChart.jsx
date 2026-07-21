/**
 * NDVI Time Series Chart
 * Displays vegetation index (NDVI, EVI, LSWI) over the growing season.
 */
import React, { useState } from 'react';
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart,
} from 'recharts';

const COLORS = {
  ndvi: '#22c55e',
  evi: '#3b82f6',
  lswi: '#a78bfa',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <p className="tooltip-date">{label}</p>
        {payload.map((entry) => (
          <div key={entry.name} className="tooltip-row">
            <span className="tooltip-dot" style={{ background: entry.color }} />
            <span>{entry.name.toUpperCase()}: <strong>{entry.value?.toFixed(3)}</strong></span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function NDVIChart({ timeSeries }) {
  const [activeIndices, setActiveIndices] = useState({ ndvi: true, evi: true, lswi: false });

  if (!timeSeries || timeSeries.length === 0) {
    return (
      <div className="chart-empty">
        <div className="chart-empty-icon">📡</div>
        <p>No vegetation data available</p>
      </div>
    );
  }

  // Format dates to short labels
  const data = timeSeries.map((d) => ({
    ...d,
    date: d.date ? d.date.slice(5) : '', // MM-DD
  }));

  const maxNdvi = Math.max(...data.map((d) => d.ndvi || 0));
  const peakDate = data.find((d) => d.ndvi === maxNdvi)?.date;

  const toggleIndex = (key) => {
    setActiveIndices((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="ndvi-chart-container">
      {/* Legend Toggles */}
      <div className="chart-legend-toggles">
        {Object.entries(COLORS).map(([key, color]) => (
          <button
            key={key}
            onClick={() => toggleIndex(key)}
            className={`legend-toggle ${activeIndices[key] ? 'active' : 'inactive'}`}
            style={{ '--toggle-color': color }}
          >
            <span className="legend-dot" style={{ background: color }} />
            {key.toUpperCase()}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="ndviGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[-0.3, 1.0]}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {peakDate && (
            <ReferenceLine
              x={peakDate}
              stroke="#fbbf24"
              strokeDasharray="4 2"
              label={{ value: 'Peak', fill: '#fbbf24', fontSize: 10, position: 'top' }}
            />
          )}
          <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />

          {activeIndices.ndvi && (
            <Area
              type="monotone"
              dataKey="ndvi"
              name="ndvi"
              stroke={COLORS.ndvi}
              strokeWidth={2}
              fill="url(#ndviGrad)"
              dot={false}
              activeDot={{ r: 5, fill: COLORS.ndvi }}
            />
          )}
          {activeIndices.evi && (
            <Line
              type="monotone"
              dataKey="evi"
              name="evi"
              stroke={COLORS.evi}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}
          {activeIndices.lswi && (
            <Line
              type="monotone"
              dataKey="lswi"
              name="lswi"
              stroke={COLORS.lswi}
              strokeWidth={1.5}
              strokeDasharray="4 2"
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      {/* Stats Row */}
      <div className="chart-stats">
        <div className="chart-stat">
          <span className="stat-label">Peak NDVI</span>
          <span className="stat-value" style={{ color: COLORS.ndvi }}>
            {maxNdvi.toFixed(3)}
          </span>
        </div>
        <div className="chart-stat">
          <span className="stat-label">Avg NDVI</span>
          <span className="stat-value" style={{ color: COLORS.ndvi }}>
            {(data.reduce((s, d) => s + (d.ndvi || 0), 0) / data.length).toFixed(3)}
          </span>
        </div>
        <div className="chart-stat">
          <span className="stat-label">Data Points</span>
          <span className="stat-value" style={{ color: '#94a3b8' }}>{data.length}</span>
        </div>
      </div>
    </div>
  );
}
