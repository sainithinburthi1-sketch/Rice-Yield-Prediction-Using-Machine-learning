"""
Rice Yield Forecasting API
FastAPI backend serving predictions from satellite data, weather, and soil features.

Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load or train the model when the server starts."""
    logger.info("Starting Rice Yield Forecasting API...")
    try:
        from services.prediction_service import initialize_model
        initialize_model()
    except Exception as e:
        logger.error(f"Model init failed at startup: {e}")
    yield
    logger.info("API shutting down.")


app = FastAPI(
    title="Rice Yield Forecasting API",
    description="Deep learning–based rice yield prediction using satellite, weather, and soil data.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the field")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the field")
    start_date: str = Field(..., description="Growing season start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Growing season end date (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 30.73,
                "longitude": 76.78,
                "start_date": "2024-06-01",
                "end_date": "2024-10-31",
            }
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.post("/predict", tags=["Prediction"])
async def predict_yield(request: PredictionRequest):
    """
    Main prediction endpoint.
    Fetches satellite, weather, and soil data dynamically then runs the deep learning model.
    Returns predicted yield in quintals/acre.
    """
    lat, lon = request.latitude, request.longitude
    start, end = request.start_date, request.end_date

    logger.info(f"Prediction request: ({lat}, {lon}) {start} → {end}")

    # Validate dates
    try:
        sd = datetime.strptime(start, "%Y-%m-%d")
        ed = datetime.strptime(end, "%Y-%m-%d")
        if ed <= sd:
            raise ValueError("end_date must be after start_date")
        if (ed - sd).days < 30:
            raise ValueError("Season must be at least 30 days")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Fetch all data sources in parallel
    import asyncio
    from services.gee_service import fetch_vegetation_indices
    from services.weather_service import fetch_weather_data
    from services.soil_service import fetch_soil_data
    from services.prediction_service import predict_yield as run_prediction

    vegetation_data, weather_data, soil_data = await asyncio.gather(
        asyncio.get_event_loop().run_in_executor(
            None, fetch_vegetation_indices, lat, lon, start, end
        ),
        fetch_weather_data(lat, lon, start, end),
        fetch_soil_data(lat, lon),
    )

    # Run inference
    result = run_prediction(vegetation_data, weather_data, soil_data, lat, lon)

    # Add NDVI time series to response for charts
    result["ndvi_time_series"] = vegetation_data.get("time_series", [])
    result["location"] = {"latitude": lat, "longitude": lon}
    result["season"] = {"start": start, "end": end}

    return result


@app.get("/vegetation", tags=["Data"])
async def get_vegetation_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
):
    """Fetch vegetation index time series (NDVI, EVI, LSWI) from GEE."""
    import asyncio
    from services.gee_service import fetch_vegetation_indices

    data = await asyncio.get_event_loop().run_in_executor(
        None, fetch_vegetation_indices, lat, lon, start_date, end_date
    )
    return data


@app.get("/weather", tags=["Data"])
async def get_weather_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
):
    """Fetch historical weather data from Open-Meteo."""
    from services.weather_service import fetch_weather_data, get_weather_summary
    raw = await fetch_weather_data(lat, lon, start_date, end_date)
    return get_weather_summary(raw)


@app.get("/soil", tags=["Data"])
async def get_soil_data(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
):
    """Fetch soil properties from SoilGrids."""
    from services.soil_service import fetch_soil_data, get_soil_description
    data = await fetch_soil_data(lat, lon)
    data["texture_class"] = get_soil_description(data)
    return data


@app.get("/ndvi-tile", tags=["Visualization"])
async def get_ndvi_tile(
    lat: float = Query(...),
    lon: float = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    """Get GEE NDVI tile URL for map overlay visualization."""
    from services.gee_service import get_ndvi_tile_url
    url = get_ndvi_tile_url(lat, lon, start_date, end_date)
    if url:
        return {"tile_url": url, "source": "GEE"}
    return {"tile_url": None, "source": "unavailable", "message": "GEE not authenticated"}


@app.get("/example-locations", tags=["Reference"])
async def get_example_locations():
    """Return example Indian rice-growing locations for demo."""
    return {
        "locations": [
            {"name": "Punjab (Ludhiana)", "lat": 30.90, "lon": 75.85, "avg_yield_q_acre": 42.0},
            {"name": "West Bengal (Hooghly)", "lat": 22.90, "lon": 88.39, "avg_yield_q_acre": 28.0},
            {"name": "Andhra Pradesh (Krishna)", "lat": 16.57, "lon": 80.36, "avg_yield_q_acre": 32.0},
            {"name": "Odisha (Cuttack)", "lat": 20.46, "lon": 85.88, "avg_yield_q_acre": 16.0},
            {"name": "Tamil Nadu (Thanjavur)", "lat": 10.79, "lon": 79.14, "avg_yield_q_acre": 36.0},
            {"name": "Haryana (Karnal)", "lat": 29.69, "lon": 76.98, "avg_yield_q_acre": 38.0},
            {"name": "Bihar (Patna)", "lat": 25.59, "lon": 85.13, "avg_yield_q_acre": 20.0},
            {"name": "Uttar Pradesh (Varanasi)", "lat": 25.32, "lon": 82.97, "avg_yield_q_acre": 24.0},
        ]
    }
