"""
Weather Service
Fetches historical weather data from the Open-Meteo API (free, no API key required).
Covers temperature, precipitation, humidity, and solar radiation
over the rice growing season.
"""
import logging
from datetime import datetime
from typing import Dict, Any

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


async def fetch_weather_data(
    lat: float, lon: float, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    Fetch hourly & daily weather data from Open-Meteo historical archive.
    Returns raw API response dict.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,shortwave_radiation",
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration",
        "timezone": "Asia/Kolkata",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()
            data["source"] = "open-meteo"
            return data
    except Exception as e:
        logger.warning(f"Open-Meteo API error: {e}. Using simulated weather.")
        return _simulate_weather(lat, lon, start_date, end_date)


def _simulate_weather(lat: float, lon: float, start_date: str, end_date: str) -> Dict[str, Any]:
    """Generate realistic synthetic weather data for Indian rice-growing regions."""
    import random
    import math
    from datetime import timedelta

    random.seed(int(abs(lat * 50) + abs(lon * 50)))

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days + 1

    # Day-by-day simulation
    daily_precip = []
    daily_temp_max = []
    daily_temp_min = []
    hourly_temp = []
    hourly_humidity = []
    hourly_solar = []

    for d in range(total_days):
        t = d / max(total_days, 1)
        # Monsoon pattern: peak precipitation mid-season
        precip = max(0, random.gauss(12 * math.sin(math.pi * t) + 2, 6))
        tmax = random.gauss(34 - 4 * math.sin(math.pi * t), 2)
        tmin = random.gauss(24 - 3 * math.sin(math.pi * t), 1.5)
        daily_precip.append(round(precip, 1))
        daily_temp_max.append(round(tmax, 1))
        daily_temp_min.append(round(tmin, 1))

        # 24 hourly readings per day
        for h in range(24):
            temp = tmin + (tmax - tmin) * math.sin(math.pi * (h - 6) / 12) if 6 <= h <= 18 else tmin
            hourly_temp.append(round(temp, 1))
            hourly_humidity.append(round(random.gauss(72, 10), 1))
            solar = max(0, random.gauss(20, 5)) if 6 <= h <= 18 else 0.0
            hourly_solar.append(round(solar, 1))

    return {
        "source": "simulated",
        "latitude": lat,
        "longitude": lon,
        "hourly": {
            "temperature_2m": hourly_temp,
            "relative_humidity_2m": hourly_humidity,
            "shortwave_radiation": hourly_solar,
        },
        "daily": {
            "precipitation_sum": daily_precip,
            "temperature_2m_max": daily_temp_max,
            "temperature_2m_min": daily_temp_min,
        },
    }


def get_weather_summary(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a clean summary dict for the frontend to display."""
    import numpy as np

    try:
        daily = weather_data.get("daily", {})
        hourly = weather_data.get("hourly", {})

        precip = daily.get("precipitation_sum", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        humidity = hourly.get("relative_humidity_2m", [])
        solar = hourly.get("shortwave_radiation", [])

        return {
            "total_rainfall_mm": round(float(sum(p for p in precip if p)), 1),
            "avg_temp_max_c": round(float(np.mean(tmax)) if tmax else 34.0, 1),
            "avg_temp_min_c": round(float(np.mean(tmin)) if tmin else 24.0, 1),
            "avg_humidity_pct": round(float(np.mean(humidity)) if humidity else 70.0, 1),
            "avg_solar_radiation": round(float(np.mean([s for s in solar if s > 0])) if solar else 18.5, 1),
            "rainy_days": int(sum(1 for p in precip if p and p > 1.0)),
            "source": weather_data.get("source", "unknown"),
        }
    except Exception as e:
        logger.error(f"Weather summary error: {e}")
        return {
            "total_rainfall_mm": 850.0,
            "avg_temp_max_c": 34.0,
            "avg_temp_min_c": 24.0,
            "avg_humidity_pct": 72.0,
            "avg_solar_radiation": 18.5,
            "rainy_days": 65,
            "source": "fallback",
        }
