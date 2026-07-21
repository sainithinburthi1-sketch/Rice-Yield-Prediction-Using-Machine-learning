/**
 * Rice Yield Forecasting Application
 * Main application shell with sidebar + map layout
 */
import React, { useState, useCallback } from 'react';
import MapSelector from './components/MapSelector';
import ResultPanel from './components/ResultPanel';
import NDVIChart from './components/NDVIChart';
import WeatherPanel from './components/WeatherPanel';
import SoilPanel from './components/SoilPanel';
import { predictYield } from './services/api';
import './App.css';

const TABS = [
  { id: 'result', label: 'Prediction', icon: '🌾' },
  { id: 'ndvi', label: 'Vegetation', icon: '📈' },
  { id: 'weather', label: 'Weather', icon: '🌦️' },
  { id: 'soil', label: 'Soil', icon: '🌱' },
];

// Default season: kharif rice season (Jun–Nov)
const getDefaultDates = () => {
  const now = new Date();
  const year = now.getMonth() >= 5 ? now.getFullYear() : now.getFullYear() - 1;
  return {
    start: `${year}-06-01`,
    end: `${year}-11-15`,
  };
};

export default function App() {
  const defaults = getDefaultDates();
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [startDate, setStartDate] = useState(defaults.start);
  const [endDate, setEndDate] = useState(defaults.end);
  const [activeTab, setActiveTab] = useState('result');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleLocationSelect = useCallback((loc) => {
    setSelectedLocation(loc);
    setResult(null);
    setError(null);
  }, []);

  const handlePredict = async () => {
    if (!selectedLocation) {
      alert('Please select a location on the map first.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setActiveTab('result');

    try {
      const data = await predictYield({
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lon,
        start_date: startDate,
        end_date: endDate,
      });
      setResult(data);
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Unknown error occurred';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const seasonDays = startDate && endDate
    ? Math.round((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24))
    : 0;

  return (
    <div className="app">
      {/* ─── Header ─────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-icon">🌾</span>
          <div>
            <h1 className="brand-title">Rice Yield Forecasting</h1>
            <p className="brand-subtitle">Satellite · Deep Learning · Precision Agriculture</p>
          </div>
        </div>
        <div className="header-badges">
          <span className="tech-badge">🛰️ GEE</span>
          <span className="tech-badge">🧠 Deep Learning</span>
          <span className="tech-badge">🌱 SoilGrids</span>
          <span className="tech-badge">🌦️ Open-Meteo</span>
        </div>
      </header>

      {/* ─── Main Layout ─────────────────────────────────── */}
      <main className="app-main">
        {/* Left: Map + Controls */}
        <section className="map-section">
          <div className="section-card map-card">
            <div className="card-header">
              <span className="card-icon">🗺️</span>
              <h2 className="card-title">Select Field Location</h2>
              {selectedLocation && (
                <span className="location-chip">
                  {selectedLocation.lat.toFixed(3)}°N, {selectedLocation.lon.toFixed(3)}°E
                </span>
              )}
            </div>
            <MapSelector
              selectedLocation={selectedLocation}
              onLocationSelect={handleLocationSelect}
            />
          </div>

          {/* Controls Panel */}
          <div className="section-card controls-card">
            <div className="card-header">
              <span className="card-icon">📅</span>
              <h2 className="card-title">Growing Season</h2>
              {seasonDays > 0 && (
                <span className="season-chip">{seasonDays} days</span>
              )}
            </div>

            <div className="controls-grid">
              <div className="control-group">
                <label className="control-label">Season Start</label>
                <input
                  type="date"
                  id="start-date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="date-input"
                  max={endDate}
                />
              </div>
              <div className="control-group">
                <label className="control-label">Season End</label>
                <input
                  type="date"
                  id="end-date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="date-input"
                  min={startDate}
                />
              </div>
            </div>

            {/* Quick Season Presets */}
            <div className="season-presets">
              <span className="presets-label">Quick Presets:</span>
              {[
                { label: 'Kharif 2024', start: '2024-06-01', end: '2024-11-15' },
                { label: 'Rabi 2024', start: '2024-11-01', end: '2025-04-15' },
                { label: 'Kharif 2023', start: '2023-06-01', end: '2023-11-15' },
              ].map((p) => (
                <button
                  key={p.label}
                  onClick={() => { setStartDate(p.start); setEndDate(p.end); }}
                  className="preset-btn"
                >
                  {p.label}
                </button>
              ))}
            </div>

            <button
              id="predict-btn"
              onClick={handlePredict}
              disabled={loading || !selectedLocation}
              className={`predict-btn ${loading ? 'loading' : ''} ${!selectedLocation ? 'disabled' : ''}`}
            >
              {loading ? (
                <>
                  <span className="btn-spinner" />
                  Analyzing…
                </>
              ) : (
                <>
                  <span>🚀</span>
                  Predict Rice Yield
                </>
              )}
            </button>

            {!selectedLocation && (
              <p className="predict-hint">👆 Click a location on the map to enable prediction</p>
            )}
          </div>
        </section>

        {/* Right: Results Panel */}
        <section className="results-section">
          {/* Tab Navigation */}
          <div className="tabs-nav">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.id !== 'result' && result && (
                  <span className="tab-dot" />
                )}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="section-card results-card">
            {activeTab === 'result' && (
              <ResultPanel result={result} loading={loading} error={error} />
            )}

            {activeTab === 'ndvi' && (
              <div className="tab-content">
                <div className="card-header">
                  <span className="card-icon">📈</span>
                  <h2 className="card-title">Vegetation Index Time Series</h2>
                </div>
                <p className="tab-description">
                  NDVI, EVI, and LSWI derived from Sentinel-2 satellite imagery over the growing season.
                </p>
                <NDVIChart timeSeries={result?.ndvi_time_series} />
              </div>
            )}

            {activeTab === 'weather' && (
              <div className="tab-content">
                <div className="card-header">
                  <span className="card-icon">🌦️</span>
                  <h2 className="card-title">Growing Season Weather</h2>
                </div>
                <p className="tab-description">
                  Historical weather data from Open-Meteo for the selected location and season.
                </p>
                <WeatherPanel weather={result?.weather_summary} />
              </div>
            )}

            {activeTab === 'soil' && (
              <div className="tab-content">
                <div className="card-header">
                  <span className="card-icon">🌱</span>
                  <h2 className="card-title">Soil Properties</h2>
                </div>
                <p className="tab-description">
                  Soil texture, organic carbon, pH, and physical properties from SoilGrids ISRIC at 0–30 cm depth.
                </p>
                <SoilPanel soil={result?.soil_summary} />
              </div>
            )}
          </div>
        </section>
      </main>

      {/* ─── Footer ─────────────────────────────────────── */}
      <footer className="app-footer">
        <span>Rice Yield Forecasting System • Deep Learning + Remote Sensing</span>
        <span>Data: Sentinel-2 GEE · Open-Meteo · SoilGrids ISRIC</span>
      </footer>
    </div>
  );
}
