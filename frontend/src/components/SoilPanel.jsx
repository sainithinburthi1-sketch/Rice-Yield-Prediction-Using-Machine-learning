/**
 * Soil Panel Component
 * Displays soil properties with visual progress bars and texture classification.
 */
import React from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer,
} from 'recharts';

const SoilBar = ({ label, value, max, unit, color }) => {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="soil-bar-row">
      <div className="soil-bar-header">
        <span className="soil-bar-label">{label}</span>
        <span className="soil-bar-value" style={{ color }}>
          {typeof value === 'number' ? value.toFixed(1) : value}
          <span style={{ fontSize: '0.75em', color: '#64748b' }}> {unit}</span>
        </span>
      </div>
      <div className="soil-bar-track">
        <div
          className="soil-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
};

export default function SoilPanel({ soil }) {
  if (!soil) {
    return (
      <div className="panel-empty">
        <span>🌱</span>
        <p>Soil data not loaded</p>
      </div>
    );
  }

  const textureClass = soil.texture_class || 'Loam';
  const source = soil.source || 'unknown';

  const radarData = [
    { subject: 'Clay', value: Math.min(100, ((soil.clay || 0) / 70) * 100) },
    { subject: 'Sand', value: Math.min(100, ((soil.sand || 0) / 85) * 100) },
    { subject: 'Silt', value: Math.min(100, ((soil.silt || 0) / 60) * 100) },
    { subject: 'OC', value: Math.min(100, ((soil.organic_carbon || 0) / 5) * 100) },
    { subject: 'pH', value: Math.min(100, (((soil.ph || 7) - 4) / 5) * 100) },
  ];

  return (
    <div className="soil-panel">
      <div className="soil-texture-badge">
        <span className="soil-texture-icon">🌍</span>
        <div>
          <div className="soil-texture-label">Soil Texture</div>
          <div className="soil-texture-class">{textureClass}</div>
        </div>
      </div>

      <div className="soil-content">
        {/* Left: Radar Chart */}
        <div className="soil-radar">
          <ResponsiveContainer width="100%" height={150}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
              />
              <Radar
                dataKey="value"
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.25}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Right: Bars */}
        <div className="soil-bars">
          <SoilBar label="Clay" value={soil.clay} max={70} unit="%" color="#a78bfa" />
          <SoilBar label="Sand" value={soil.sand} max={85} unit="%" color="#f59e0b" />
          <SoilBar label="Silt" value={soil.silt} max={60} unit="%" color="#06b6d4" />
          <SoilBar label="Org. Carbon" value={soil.organic_carbon} max={5} unit="g/kg" color="#22c55e" />
          <SoilBar label="pH" value={soil.ph} max={9} unit="" color="#f97316" />
          <SoilBar label="Bulk Density" value={soil.bulk_density} max={2} unit="g/cm³" color="#94a3b8" />
        </div>
      </div>

      <div className="data-source-badge">
        <span className={`source-dot ${source === 'simulated' ? 'simulated' : 'live'}`} />
        {source === 'soilgrids' ? '📡 Live — SoilGrids ISRIC' : '🔄 Simulated soil data'}
      </div>
    </div>
  );
}
