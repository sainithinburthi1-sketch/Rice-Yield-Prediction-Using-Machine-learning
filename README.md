# Rice Yield Forecasting Using Machine Learning

> Deep Learning + Remote Sensing for Precision Agriculture

An end-to-end AI application that predicts **rice crop yield in quintals per acre** using:
- 🛰️ **Satellite Imagery** (Google Earth Engine / Sentinel-2) → NDVI, EVI, LSWI
- 🌦️ **Weather Data** (Open-Meteo API) → Temperature, Rainfall, Humidity, Solar Radiation
- 🌱 **Soil Data** (SoilGrids ISRIC) → Clay, Sand, Organic Carbon, pH, Bulk Density
- 🧠 **Deep Learning** (TensorFlow/Keras) → Dense neural network trained on synthetic Indian crop data

---

## Project Structure

```
Rice Yield Forecasting/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── requirements.txt
│   ├── services/
│   │   ├── gee_service.py       # Google Earth Engine + simulation
│   │   ├── weather_service.py   # Open-Meteo weather data
│   │   ├── soil_service.py      # SoilGrids soil data
│   │   └── prediction_service.py# ML inference pipeline
│   ├── models/
│   │   └── train_model.py       # Auto-trains on first run
│   └── utils/
│       └── feature_engineering.py
└── frontend/
    └── src/
        ├── App.jsx              # Main application
        ├── components/
        │   ├── MapSelector.jsx  # Interactive Leaflet map
        │   ├── ResultPanel.jsx  # Yield prediction + gauge
        │   ├── NDVIChart.jsx    # Vegetation time series
        │   ├── WeatherPanel.jsx # Weather summary cards
        │   └── SoilPanel.jsx    # Soil properties + radar chart
        └── services/
            └── api.js           # Backend API calls
```

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The model trains automatically on first startup (~30 seconds).

### Makefile

If you have `make` installed, you can use the top-level Makefile to install dependencies and start the app:

```bash
make install
make backend
make frontend
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Google Earth Engine Setup (Optional)

The app works without GEE using realistic simulation. To enable real satellite imagery:

**Option A — Service Account:**
```bash
set GEE_SERVICE_ACCOUNT_EMAIL=your-sa@project.iam.gserviceaccount.com
set GEE_SERVICE_ACCOUNT_KEY=path/to/key.json
```

**Option B — Interactive Auth:**
```python
import ee
ee.Authenticate()
ee.Initialize()
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/predict` | Full yield prediction |
| GET | `/vegetation` | NDVI/EVI/LSWI time series |
| GET | `/weather` | Weather summary |
| GET | `/soil` | Soil properties |
| GET | `/ndvi-tile` | GEE tile URL for map |
| GET | `/example-locations` | Demo Indian locations |

---

## Yield Ranges (India)

| Category | Yield | Example Regions |
|----------|-------|-----------------|
| Low | < 15 q/acre | Rainfed Odisha, Assam |
| Below Average | 15–25 q/acre | Bihar, parts of UP |
| Average | 25–35 q/acre | West Bengal, AP |
| Good | 35–42 q/acre | Tamil Nadu, Haryana |
| Excellent | > 42 q/acre | Punjab (irrigated) |

*1 quintal = 100 kg. National average: ~26 q/acre (2023)*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, Leaflet.js, Recharts |
| Backend | Python FastAPI + Uvicorn |
| ML Model | TensorFlow/Keras (Dense + BN + Dropout) |
| Satellite | Google Earth Engine (Sentinel-2) |
| Weather | Open-Meteo Historical Archive API |
| Soil | SoilGrids ISRIC REST API |
