"""
Google Earth Engine Service
Fetches Sentinel-2 satellite imagery and computes vegetation indices
(NDVI, EVI, LSWI) for a given location and date range.

Falls back to realistic simulated data if GEE is not authenticated.
"""
import os
import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import GEE — gracefully degrade if not installed/authenticated
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    logger.warning("earthengine-api not installed. Running in simulation mode.")


def initialize_gee() -> bool:
    """
    Attempt to initialize Google Earth Engine.
    Supports service account key via GEE_SERVICE_ACCOUNT_KEY env var,
    or falls back to ee.Initialize() with default credentials.
    """
    if not GEE_AVAILABLE:
        return False
    try:
        key_path = os.getenv("GEE_SERVICE_ACCOUNT_KEY")
        if key_path and os.path.exists(key_path):
            credentials = ee.ServiceAccountCredentials(
                email=os.getenv("GEE_SERVICE_ACCOUNT_EMAIL", ""),
                key_file=key_path,
            )
            ee.Initialize(credentials)
        else:
            ee.Initialize()
        logger.info("Google Earth Engine initialized successfully.")
        return True
    except Exception as e:
        logger.warning(f"GEE initialization failed: {e}. Using simulation mode.")
        return False


# Try GEE initialization at module load
GEE_ACTIVE = initialize_gee()


# ---------------------------------------------------------------------------
# Vegetation Index Computation via GEE
# ---------------------------------------------------------------------------

def _get_sentinel2_collection(lat: float, lon: float, start_date: str, end_date: str):
    """Return a cloud-filtered Sentinel-2 Surface Reflectance collection."""
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(5000)  # 5 km buffer

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(region)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    )
    return collection, region


def _add_indices(image):
    """Add NDVI, EVI, and LSWI bands to a Sentinel-2 image."""
    nir = image.select("B8")
    red = image.select("B4")
    blue = image.select("B2")
    swir = image.select("B11")

    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    evi = (
        nir.subtract(red)
        .multiply(2.5)
        .divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1))
        .rename("EVI")
    )
    lswi = nir.subtract(swir).divide(nir.add(swir)).rename("LSWI")

    return image.addBands([ndvi, evi, lswi])


def fetch_vegetation_indices_gee(
    lat: float, lon: float, start_date: str, end_date: str
) -> Dict[str, Any]:
    """Fetch real vegetation index time series from Google Earth Engine."""
    try:
        collection, region = _get_sentinel2_collection(lat, lon, start_date, end_date)
        with_indices = collection.map(_add_indices)

        def extract_values(image):
            date = image.date().format("YYYY-MM-dd")
            stats = image.select(["NDVI", "EVI", "LSWI"]).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=30,
                maxPixels=1e9,
            )
            return ee.Feature(None, {
                "date": date,
                "ndvi": stats.get("NDVI"),
                "evi": stats.get("EVI"),
                "lswi": stats.get("LSWI"),
            })

        feature_collection = with_indices.map(extract_values)
        result = feature_collection.getInfo()

        time_series = []
        for feat in result.get("features", []):
            props = feat.get("properties", {})
            time_series.append({
                "date": props.get("date"),
                "ndvi": props.get("ndvi") or 0.0,
                "evi": props.get("evi") or 0.0,
                "lswi": props.get("lswi") or 0.0,
            })

        time_series.sort(key=lambda x: x.get("date", ""))
        return {"source": "GEE", "time_series": time_series}

    except Exception as e:
        logger.error(f"GEE vegetation fetch error: {e}")
        return _simulate_vegetation_indices(lat, lon, start_date, end_date)


def get_ndvi_tile_url(lat: float, lon: float, start_date: str, end_date: str) -> Optional[str]:
    """Get a GEE tile URL for NDVI visualization on the map."""
    if not GEE_ACTIVE:
        return None
    try:
        collection, region = _get_sentinel2_collection(lat, lon, start_date, end_date)
        ndvi_image = (
            collection.map(_add_indices)
            .select("NDVI")
            .mean()
            .clip(region)
        )
        vis_params = {
            "min": -0.1,
            "max": 0.9,
            "palette": ["#d73027", "#fee08b", "#1a9850"],
        }
        map_id = ndvi_image.getMapId(vis_params)
        return map_id.get("tile_fetcher").url_format
    except Exception as e:
        logger.error(f"GEE tile URL error: {e}")
        return None


# ---------------------------------------------------------------------------
# Simulation Fallback
# ---------------------------------------------------------------------------

def _simulate_vegetation_indices(
    lat: float, lon: float, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    Generate realistic synthetic NDVI/EVI/LSWI time series following
    a typical rice growing-season phenology curve (transplant → heading → harvest).
    """
    random.seed(int(abs(lat * 100) + abs(lon * 100)))

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days

    # Sentinel-2 revisit ~5 days
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=5)

    time_series = []
    for d in dates:
        day = (d - start).days
        t = day / max(total_days, 1)

        # Bell-shaped NDVI phenology: peaks at ~60% of season (heading stage)
        ndvi_base = 0.7 * math.sin(math.pi * t) + 0.15
        ndvi = max(0.05, min(0.95, ndvi_base + random.gauss(0, 0.03)))
        evi = max(0.02, ndvi * 0.82 + random.gauss(0, 0.02))
        lswi = max(-0.2, ndvi * 0.55 - 0.05 + random.gauss(0, 0.02))

        time_series.append({
            "date": d.strftime("%Y-%m-%d"),
            "ndvi": round(ndvi, 4),
            "evi": round(evi, 4),
            "lswi": round(lswi, 4),
        })

    return {"source": "simulated", "time_series": time_series}


def fetch_vegetation_indices(
    lat: float, lon: float, start_date: str, end_date: str
) -> Dict[str, Any]:
    """Main entry point: uses GEE if available, else simulation."""
    if GEE_ACTIVE:
        return fetch_vegetation_indices_gee(lat, lon, start_date, end_date)
    return _simulate_vegetation_indices(lat, lon, start_date, end_date)
