/**
 * MapSelector Component
 * Interactive Leaflet map for selecting field location.
 * Shows India by default with example location markers.
 */
import React from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, Popup, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon path issue with Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const SELECTED_ICON = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const EXAMPLE_ICON = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [20, 33],
  iconAnchor: [10, 33],
  popupAnchor: [1, -28],
  shadowSize: [33, 33],
});

const EXAMPLE_LOCATIONS = [
  { name: 'Punjab (Ludhiana)', lat: 30.90, lon: 75.85, avg: 42.0 },
  { name: 'West Bengal', lat: 22.90, lon: 88.39, avg: 28.0 },
  { name: 'Andhra Pradesh', lat: 16.57, lon: 80.36, avg: 32.0 },
  { name: 'Tamil Nadu', lat: 10.79, lon: 79.14, avg: 36.0 },
  { name: 'Odisha', lat: 20.46, lon: 85.88, avg: 16.0 },
  { name: 'Haryana', lat: 29.69, lon: 76.98, avg: 38.0 },
  { name: 'Bihar', lat: 25.59, lon: 85.13, avg: 20.0 },
  { name: 'Uttar Pradesh', lat: 25.32, lon: 82.97, avg: 24.0 },
];

// Component to handle map click events
function ClickHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      onLocationSelect({ lat: +lat.toFixed(6), lon: +lng.toFixed(6) });
    },
  });
  return null;
}

export default function MapSelector({ selectedLocation, onLocationSelect }) {

  return (
    <div className="map-wrapper">
      <MapContainer
        center={[22.5937, 80.9629]}  // Center of India
        zoom={5}
        className="leaflet-map"
        zoomControl={false}
      >
        {/* Dark satellite tile layer */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          maxZoom={20}
        />
        {/* Satellite overlay (optional) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution='&copy; Esri'
          opacity={0.35}
          maxZoom={20}
        />

        <ZoomControl position="bottomright" />
        <ClickHandler onLocationSelect={onLocationSelect} />

        {/* Example location markers */}
        {EXAMPLE_LOCATIONS.map((loc) => (
          <Marker
            key={loc.name}
            position={[loc.lat, loc.lon]}
            icon={EXAMPLE_ICON}
            eventHandlers={{
              click: () => onLocationSelect({ lat: loc.lat, lon: loc.lon }),
            }}
          >
            <Popup className="map-popup">
              <div className="popup-content">
                <strong>{loc.name}</strong>
                <p>Avg Yield: <span className="popup-yield">{loc.avg} q/acre</span></p>
                <button
                  onClick={() => onLocationSelect({ lat: loc.lat, lon: loc.lon })}
                  className="popup-select-btn"
                >
                  Select this location
                </button>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Selected location marker */}
        {selectedLocation && (
          <Marker
            position={[selectedLocation.lat, selectedLocation.lon]}
            icon={SELECTED_ICON}
          >
            <Popup className="map-popup">
              <div className="popup-content">
                <strong>📍 Selected Field</strong>
                <p>Lat: {selectedLocation.lat.toFixed(4)}</p>
                <p>Lon: {selectedLocation.lon.toFixed(4)}</p>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map Overlay Hint */}
      <div className="map-hint">
        <span>🖱️</span> Click anywhere to select your rice field
      </div>

      {/* Coordinates display */}
      {selectedLocation && (
        <div className="map-coords">
          📍 {selectedLocation.lat.toFixed(4)}°N, {selectedLocation.lon.toFixed(4)}°E
        </div>
      )}
    </div>
  );
}
