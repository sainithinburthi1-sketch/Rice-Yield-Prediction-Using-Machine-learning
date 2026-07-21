"""
Feature Engineering Utilities
Assembles raw GEE, weather, and soil data into model-ready feature vectors.
"""
import numpy as np
from typing import List, Dict, Any, Optional


# Expected feature order for the model
VEGETATION_FEATURES = ["ndvi_mean", "ndvi_max", "ndvi_std", "evi_mean", "lswi_mean"]
WEATHER_FEATURES = [
    "temp_mean", "temp_max", "temp_min",
    "precip_total", "precip_days",
    "humidity_mean",
    "solar_rad_mean",
]
SOIL_FEATURES = ["clay", "sand", "silt", "organic_carbon", "ph", "bulk_density"]

ALL_FEATURES = VEGETATION_FEATURES + WEATHER_FEATURES + SOIL_FEATURES


def compute_vegetation_stats(ndvi_series: List[float], evi_series: List[float], lswi_series: List[float]) -> Dict[str, float]:
    """Compute summary statistics from vegetation index time series."""
    ndvi = np.array(ndvi_series) if ndvi_series else np.array([0.3])
    evi = np.array(evi_series) if evi_series else np.array([0.25])
    lswi = np.array(lswi_series) if lswi_series else np.array([0.1])

    return {
        "ndvi_mean": float(np.nanmean(ndvi)),
        "ndvi_max": float(np.nanmax(ndvi)),
        "ndvi_std": float(np.nanstd(ndvi)),
        "evi_mean": float(np.nanmean(evi)),
        "lswi_mean": float(np.nanmean(lswi)),
    }


def aggregate_weather(weather_data: Dict[str, Any]) -> Dict[str, float]:
    """Aggregate raw daily weather data to summary statistics."""
    try:
        hourly = weather_data.get("hourly", {})
        daily = weather_data.get("daily", {})

        temp_2m = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        solar_rad = hourly.get("shortwave_radiation", [])

        precip = daily.get("precipitation_sum", [])
        daily_temp_max = daily.get("temperature_2m_max", [])
        daily_temp_min = daily.get("temperature_2m_min", [])

        temp_arr = np.array(temp_2m) if temp_2m else np.array([28.0])
        precip_arr = np.array(precip) if precip else np.array([5.0])
        hum_arr = np.array(humidity) if humidity else np.array([70.0])
        solar_arr = np.array(solar_rad) if solar_rad else np.array([18.0 / 0.0864])

        # Daily temp max/min average over the season
        tmax = float(np.nanmean(daily_temp_max)) if daily_temp_max else float(np.nanmax(temp_arr))
        tmin = float(np.nanmean(daily_temp_min)) if daily_temp_min else float(np.nanmin(temp_arr))

        # Convert hourly avg W/m2 to daily avg MJ/m2/day
        solar_avg_w_m2 = float(np.nanmean(solar_arr))
        solar_rad_mean = solar_avg_w_m2 * 0.0864

        return {
            "temp_mean": float(np.nanmean(temp_arr)),
            "temp_max": tmax,
            "temp_min": tmin,
            "precip_total": float(np.nansum(precip_arr)),
            "precip_days": int(np.sum(precip_arr > 1.0)),
            "humidity_mean": float(np.nanmean(hum_arr)),
            "solar_rad_mean": solar_rad_mean,
        }
    except Exception:
        return {
            "temp_mean": 28.0, "temp_max": 35.0, "temp_min": 22.0,
            "precip_total": 800.0, "precip_days": 60,
            "humidity_mean": 72.0, "solar_rad_mean": 18.5,
        }



def normalize_soil(soil_data: Dict[str, Any]) -> Dict[str, float]:
    """Extract and normalize soil properties."""
    defaults = {
        "clay": 30.0, "sand": 40.0, "silt": 30.0,
        "organic_carbon": 1.2, "ph": 6.5, "bulk_density": 1.3,
    }
    result = {}
    for key, default in defaults.items():
        val = soil_data.get(key, default)
        result[key] = float(val) if val is not None else default
    return result


def assemble_feature_vector(
    vegetation_stats: Dict[str, float],
    weather_aggregated: Dict[str, float],
    soil_normalized: Dict[str, float],
) -> np.ndarray:
    """Combine all features into a single flat numpy array."""
    feature_vec = []
    for feat in ALL_FEATURES:
        val = vegetation_stats.get(feat) or weather_aggregated.get(feat) or soil_normalized.get(feat, 0.0)
        feature_vec.append(float(val) if val is not None else 0.0)
    return np.array(feature_vec, dtype=np.float32)


def scale_features(feature_vec: np.ndarray, scaler=None) -> np.ndarray:
    """Apply standard scaling if a scaler is provided."""
    if scaler is not None:
        return scaler.transform(feature_vec.reshape(1, -1)).flatten()
    # Simple manual normalization ranges (calibrated to typical ranges)
    ranges = {
        "ndvi_mean": (0.0, 1.0), "ndvi_max": (0.0, 1.0), "ndvi_std": (0.0, 0.5),
        "evi_mean": (0.0, 1.0), "lswi_mean": (-0.5, 0.8),
        "temp_mean": (15.0, 40.0), "temp_max": (20.0, 50.0), "temp_min": (10.0, 35.0),
        "precip_total": (0.0, 2000.0), "precip_days": (0.0, 120.0),
        "humidity_mean": (30.0, 100.0), "solar_rad_mean": (5.0, 30.0),
        "clay": (5.0, 70.0), "sand": (5.0, 85.0), "silt": (5.0, 60.0),
        "organic_carbon": (0.1, 5.0), "ph": (4.0, 9.0), "bulk_density": (0.8, 1.9),
    }
    scaled = []
    for i, feat in enumerate(ALL_FEATURES):
        lo, hi = ranges.get(feat, (0.0, 1.0))
        scaled.append((feature_vec[i] - lo) / (hi - lo + 1e-8))
    return np.clip(np.array(scaled, dtype=np.float32), 0.0, 1.0)
