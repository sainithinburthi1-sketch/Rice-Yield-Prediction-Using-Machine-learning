/**
 * Result Panel Component
 * Shows the yield prediction with animated gauge, confidence interval,
 * yield category, and agronomic recommendations.
 */
import React, { useEffect, useState, useRef } from 'react';

const YIELD_RANGES = [
  { label: 'Low', min: 0, max: 15, color: '#ef4444', gradient: 'from-red-500' },
  { label: 'Below Avg', min: 15, max: 25, color: '#f97316', gradient: 'from-orange-500' },
  { label: 'Average', min: 25, max: 35, color: '#eab308', gradient: 'from-yellow-500' },
  { label: 'Good', min: 35, max: 42, color: '#22c55e', gradient: 'from-green-500' },
  { label: 'Excellent', min: 42, max: 55, color: '#10b981', gradient: 'from-emerald-500' },
];

function YieldGauge({ value, maxVal = 55 }) {
  const [displayVal, setDisplayVal] = useState(0);
  const animRef = useRef(null);

  useEffect(() => {
    setDisplayVal(0);
    let start = null;
    const duration = 1500;

    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplayVal(value * eased);
      if (progress < 1) animRef.current = requestAnimationFrame(step);
    };

    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, [value]);

  const range = YIELD_RANGES.find((r) => value >= r.min && value < r.max) || YIELD_RANGES[4];
  const percentage = (displayVal / maxVal) * 100;

  // SVG arc parameters
  const R = 80;
  const cx = 100, cy = 100;
  const startAngle = -220;
  const sweepAngle = 260;

  const toRad = (deg) => (deg * Math.PI) / 180;
  const arcPath = (cx, cy, r, startDeg, endDeg) => {
    const start = {
      x: cx + r * Math.cos(toRad(startDeg)),
      y: cy + r * Math.sin(toRad(startDeg)),
    };
    const end = {
      x: cx + r * Math.cos(toRad(endDeg)),
      y: cy + r * Math.sin(toRad(endDeg)),
    };
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
  };

  const fillEnd = startAngle + (percentage / 100) * sweepAngle;

  return (
    <div className="gauge-container">
      <svg viewBox="0 0 200 140" className="gauge-svg">
        {/* Background arc */}
        <path
          d={arcPath(cx, cy, R, startAngle, startAngle + sweepAngle)}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="14"
          strokeLinecap="round"
        />
        {/* Colored range segments */}
        {YIELD_RANGES.map((seg) => {
          const segStart = startAngle + (seg.min / maxVal) * sweepAngle;
          const segEnd = startAngle + (seg.max / maxVal) * sweepAngle;
          return (
            <path
              key={seg.label}
              d={arcPath(cx, cy, R, segStart, segEnd)}
              fill="none"
              stroke={seg.color}
              strokeWidth="4"
              strokeLinecap="butt"
              opacity={0.25}
            />
          );
        })}
        {/* Active fill arc */}
        {displayVal > 0 && (
          <path
            d={arcPath(cx, cy, R, startAngle, fillEnd)}
            fill="none"
            stroke={range.color}
            strokeWidth="14"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 6px ${range.color})` }}
          />
        )}
        {/* Needle dot */}
        <circle
          cx={cx + R * Math.cos(toRad(fillEnd))}
          cy={cy + R * Math.sin(toRad(fillEnd))}
          r="6"
          fill={range.color}
          style={{ filter: `drop-shadow(0 0 8px ${range.color})` }}
        />
        {/* Center value */}
        <text x={cx} y={cy - 5} textAnchor="middle" fill="white" fontSize="28" fontWeight="bold">
          {displayVal.toFixed(1)}
        </text>
        <text x={cx} y={cy + 16} textAnchor="middle" fill="#94a3b8" fontSize="10">
          q/acre
        </text>
      </svg>

      <div className="gauge-category" style={{ color: range.color }}>
        <div className="category-dot" style={{ background: range.color }} />
        {range.label} Yield
      </div>
    </div>
  );
}

export default function ResultPanel({ result, loading, error }) {
  if (loading) {
    return (
      <div className="result-loading">
        <div className="loading-spinner" />
        <div className="loading-steps">
          <p className="loading-title">Analyzing Satellite & Field Data...</p>
          <p className="loading-sub">🛰️ Fetching Sentinel-2 imagery</p>
          <p className="loading-sub">🌦️ Processing weather history</p>
          <p className="loading-sub">🌱 Querying soil properties</p>
          <p className="loading-sub">🧠 Running deep learning model</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="result-error">
        <div className="error-icon">⚠️</div>
        <p className="error-title">Prediction Failed</p>
        <p className="error-msg">{error}</p>
        <p className="error-hint">Make sure the backend server is running on port 8000.</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-placeholder">
        <div className="placeholder-icon">🌾</div>
        <h3>Select a field location</h3>
        <p>Click anywhere on the map to select your rice field, choose a growing season, and run the prediction.</p>
        <div className="placeholder-steps">
          <div className="step-item"><span className="step-num">1</span> Click location on map</div>
          <div className="step-item"><span className="step-num">2</span> Set season dates</div>
          <div className="step-item"><span className="step-num">3</span> Click "Predict Yield"</div>
        </div>
      </div>
    );
  }

  const { yield_quintals_per_acre, confidence_interval, yield_kg_per_hectare,
          recommendations, data_sources } = result;

  return (
    <div className="result-panel">
      {/* Main Gauge */}
      <YieldGauge value={yield_quintals_per_acre} />

      {/* Key Metrics */}
      <div className="result-metrics">
        <div className="metric-box">
          <span className="metric-label">Confidence Range</span>
          <span className="metric-value">
            {confidence_interval?.low} – {confidence_interval?.high}
            <span className="metric-unit"> q/acre</span>
          </span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Equivalent</span>
          <span className="metric-value">
            {yield_kg_per_hectare?.toLocaleString()}
            <span className="metric-unit"> kg/ha</span>
          </span>
        </div>
      </div>

      {/* Vegetation Stats */}
      {result.vegetation_stats && (
        <div className="veg-stats-row">
          <div className="veg-stat">
            <span className="veg-label">NDVI</span>
            <span className="veg-value ndvi">{result.vegetation_stats.ndvi_mean?.toFixed(3)}</span>
          </div>
          <div className="veg-stat">
            <span className="veg-label">EVI</span>
            <span className="veg-value evi">{result.vegetation_stats.evi_mean?.toFixed(3)}</span>
          </div>
          <div className="veg-stat">
            <span className="veg-label">LSWI</span>
            <span className="veg-value lswi">{result.vegetation_stats.lswi_mean?.toFixed(3)}</span>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="recommendations">
          <h4 className="rec-title">Agronomic Insights</h4>
          {recommendations.map((rec, i) => (
            <div key={i} className="rec-item">{rec}</div>
          ))}
        </div>
      )}

      {/* Data Source Badges */}
      {data_sources && (
        <div className="source-badges">
          {Object.entries(data_sources).map(([key, val]) => (
            <span key={key} className={`source-chip ${val === 'simulated' ? 'sim' : 'live'}`}>
              {key}: {val}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
