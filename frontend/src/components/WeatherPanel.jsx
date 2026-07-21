/**
 * Weather Panel Component
 * Displays weather summary cards for the growing season.
 */
import React from 'react';

const MetricCard = ({ icon, label, value, unit, color }) => (
  <div className="weather-card" style={{ '--card-accent': color }}>
    <div className="weather-card-icon">{icon}</div>
    <div className="weather-card-content">
      <span className="weather-card-label">{label}</span>
      <span className="weather-card-value" style={{ color }}>
        {value}
        <span className="weather-card-unit">{unit}</span>
      </span>
    </div>
  </div>
);

export default function WeatherPanel({ weather }) {
  if (!weather) {
    return (
      <div className="panel-empty">
        <span>🌦️</span>
        <p>Weather data not loaded</p>
      </div>
    );
  }

  const metrics = [
    {
      icon: '🌡️',
      label: 'Avg Temperature',
      value: weather.avg_temp_max_c ?? weather.avg_temperature_c ?? '—',
      unit: '°C',
      color: '#f97316',
    },
    {
      icon: '🌧️',
      label: 'Total Rainfall',
      value: weather.total_rainfall_mm ?? '—',
      unit: ' mm',
      color: '#3b82f6',
    },
    {
      icon: '💧',
      label: 'Rainy Days',
      value: weather.rainy_days ?? '—',
      unit: ' days',
      color: '#06b6d4',
    },
    {
      icon: '💨',
      label: 'Avg Humidity',
      value: weather.avg_humidity_pct ?? '—',
      unit: '%',
      color: '#8b5cf6',
    },
    {
      icon: '☀️',
      label: 'Solar Radiation',
      value: weather.avg_solar_radiation ?? '—',
      unit: ' W/m²',
      color: '#eab308',
    },
  ];

  const source = weather.source || 'unknown';

  return (
    <div className="weather-panel">
      <div className="weather-grid">
        {metrics.map((m) => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>
      <div className="data-source-badge">
        <span className={`source-dot ${source === 'simulated' ? 'simulated' : 'live'}`} />
        {source === 'open-meteo' ? '📡 Live — Open-Meteo' : '🔄 Simulated data'}
      </div>
    </div>
  );
}
