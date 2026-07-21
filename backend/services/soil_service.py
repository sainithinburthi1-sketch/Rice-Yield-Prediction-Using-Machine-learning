"""
Soil Service
Fetches soil property data from the SoilGrids REST API (ISRIC World Soil Information).
Returns clay, sand, silt, organic carbon, pH, and bulk density for a given location.
"""
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"


async def fetch_soil_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch soil properties from SoilGrids API at 0–30 cm depth.
    Falls back to simulated values if API is unavailable.
    """
    properties = ["clay", "sand", "silt", "oc", "phh2o", "bdod"]
    params = {
        "lon": lon,
        "lat": lat,
        "property": properties,
        "depth": "0-30cm",
        "value": "mean",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(SOILGRIDS_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return _parse_soilgrids_response(data)
    except Exception as e:
        logger.warning(f"SoilGrids API error: {e}. Using simulated soil data.")
        return _simulate_soil_data(lat, lon)


def _parse_soilgrids_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the SoilGrids API response into a flat dict with physical units."""
    result = {"source": "soilgrids"}
    try:
        layers = data.get("properties", {}).get("layers", [])
        for layer in layers:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                # Get the 0-30cm depth value
                val = depths[0].get("values", {}).get("mean")
                unit_factor = layer.get("unit_measure", {}).get("d_factor", 1)
                if val is not None:
                    actual_val = val / unit_factor
                    if name == "clay":
                        result["clay"] = round(actual_val, 1)        # g/kg → %
                    elif name == "sand":
                        result["sand"] = round(actual_val, 1)
                    elif name == "silt":
                        result["silt"] = round(actual_val, 1)
                    elif name == "oc":
                        result["organic_carbon"] = round(actual_val, 2)  # g/kg
                    elif name == "phh2o":
                        result["ph"] = round(actual_val / 10, 2)     # pH × 10
                    elif name == "bdod":
                        result["bulk_density"] = round(actual_val / 100, 2)  # cg/cm³
    except Exception as e:
        logger.error(f"SoilGrids parse error: {e}")

    # Fill any missing values with defaults
    defaults = {"clay": 28.0, "sand": 42.0, "silt": 30.0,
                 "organic_carbon": 1.1, "ph": 6.4, "bulk_density": 1.35}
    for k, v in defaults.items():
        result.setdefault(k, v)

    return result


def _simulate_soil_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Generate location-aware synthetic soil data.
    Broadly realistic for Indian agricultural regions.
    """
    import random
    random.seed(int(abs(lat * 77) + abs(lon * 33)))

    # Indo-Gangetic Plain → heavier clay, alluvial
    # Deccan → red soils, lower OC
    # Coastal → sandy, acidic
    is_gangetic = 20 < lat < 32 and 72 < lon < 92
    is_coastal = lon > 79 and lat < 18

    clay = random.gauss(35 if is_gangetic else 22, 5)
    sand = random.gauss(25 if is_gangetic else 45, 7)
    silt = 100 - clay - sand
    oc = random.gauss(1.4 if is_gangetic else 0.9, 0.3)
    ph = random.gauss(6.5 if not is_coastal else 5.8, 0.4)
    bd = random.gauss(1.30 if is_gangetic else 1.45, 0.1)

    return {
        "source": "simulated",
        "clay": round(max(5, min(70, clay)), 1),
        "sand": round(max(5, min(80, sand)), 1),
        "silt": round(max(5, min(60, silt)), 1),
        "organic_carbon": round(max(0.1, min(5.0, oc)), 2),
        "ph": round(max(4.0, min(9.0, ph)), 2),
        "bulk_density": round(max(0.8, min(1.9, bd)), 2),
    }


def get_soil_description(soil_data: Dict[str, Any]) -> str:
    """Return a human-readable soil texture classification."""
    clay = soil_data.get("clay", 28)
    sand = soil_data.get("sand", 42)
    silt = soil_data.get("silt", 30)

    if clay > 40:
        return "Clay"
    elif clay > 27 and silt > 28:
        return "Clay Loam"
    elif sand > 70:
        return "Sandy"
    elif silt > 50:
        return "Silty Loam"
    else:
        return "Loam"
