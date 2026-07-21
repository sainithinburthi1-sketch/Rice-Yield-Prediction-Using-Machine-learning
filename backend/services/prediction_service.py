"""
Prediction Service
Assembles all features and runs inference with the trained MLPRegressor model.
Returns predicted rice yield in quintals/acre with confidence interval.
"""
import os
import logging
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Global model & scaler (loaded at startup)
_model = None
_scaler = None


def initialize_model():
    """Load or train the model at app startup."""
    global _model, _scaler
    try:
        from models.train_model import load_or_train_model
        _model, _scaler = load_or_train_model()
        logger.info("Prediction model ready.")
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        _model = None
        _scaler = None


def predict_yield(
    vegetation_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    soil_data: Dict[str, Any],
    lat: float,
    lon: float,
) -> Dict[str, Any]:
    """
    Full inference pipeline:
    1. Extract features from raw data
    2. Scale features
    3. Run MLP inference
    4. Return prediction in quintals/acre with metadata
    """
    from utils.feature_engineering import (
        compute_vegetation_stats,
        aggregate_weather,
        normalize_soil,
        assemble_feature_vector,
    )

    # 1. Extract time series
    time_series = vegetation_data.get("time_series", [])
    ndvi_vals = [d["ndvi"] for d in time_series if d.get("ndvi") is not None]
    evi_vals = [d["evi"] for d in time_series if d.get("evi") is not None]
    lswi_vals = [d["lswi"] for d in time_series if d.get("lswi") is not None]

    # 2. Compute feature blocks
    veg_stats = compute_vegetation_stats(ndvi_vals, evi_vals, lswi_vals)
    weather_agg = aggregate_weather(weather_data)
    soil_norm = normalize_soil(soil_data)

    # 3. Assemble full feature vector (18 features)
    feature_vec = assemble_feature_vector(veg_stats, weather_agg, soil_norm)

    # 4. Predict
    if _model is not None and _scaler is not None:
        try:
            X_scaled = _scaler.transform(feature_vec.reshape(1, -1))
            yield_pred = float(np.clip(_model.predict(X_scaled)[0], 5.0, 55.0))

            # Bootstrap uncertainty estimate: perturb features slightly × 30
            preds = []
            rng = np.random.RandomState(42)
            for _ in range(30):
                noise = rng.normal(0, 0.03, size=feature_vec.shape)
                X_noisy = _scaler.transform((feature_vec + noise).reshape(1, -1))
                p = float(_model.predict(X_noisy)[0])
                preds.append(np.clip(p, 5.0, 55.0))

            std = np.std(preds)
            ci_low = max(5.0, yield_pred - 1.96 * std)
            ci_high = min(55.0, yield_pred + 1.96 * std)

        except Exception as e:
            logger.error(f"Model inference error: {e}")
            yield_pred, ci_low, ci_high = _rule_based_prediction(veg_stats, weather_agg, soil_norm)
    else:
        yield_pred, ci_low, ci_high = _rule_based_prediction(veg_stats, weather_agg, soil_norm)

    yield_pred = round(yield_pred, 1)
    ci_low = round(ci_low, 1)
    ci_high = round(ci_high, 1)

    # 5. Build response
    return {
        "yield_quintals_per_acre": yield_pred,
        "confidence_interval": {"low": ci_low, "high": ci_high},
        "yield_kg_per_hectare": round(yield_pred * 247.1, 0),
        "vegetation_stats": {k: round(v, 4) for k, v in veg_stats.items()},
        "weather_summary": _format_weather_summary(weather_agg),
        "soil_summary": soil_norm,
        "data_sources": {
            "vegetation": vegetation_data.get("source", "simulated"),
            "weather": weather_data.get("source", "simulated"),
            "soil": soil_data.get("source", "simulated"),
        },
        "yield_category": _categorize_yield(yield_pred),
        "recommendations": _get_recommendations(veg_stats, weather_agg, soil_norm, yield_pred),
    }


def _rule_based_prediction(veg_stats, weather_agg, soil_norm):
    """Fallback rule-based prediction when the ML model is unavailable."""
    ndvi = veg_stats.get("ndvi_mean", 0.4)
    precip = weather_agg.get("precip_total", 700)
    oc = soil_norm.get("organic_carbon", 1.0)
    temp = weather_agg.get("temp_mean", 28)

    base = 30 * ndvi
    water = 8 * min(precip / 1000, 1.0)
    temp_adj = -abs(temp - 27) * 0.4
    soil_adj = oc * 2.0

    pred = float(np.clip(base + water + temp_adj + soil_adj, 8.0, 50.0))
    return pred, pred - 3.0, pred + 3.0


def _categorize_yield(yield_q: float) -> Dict[str, str]:
    if yield_q < 15:
        return {"label": "Low", "color": "#ef4444", "description": "Below average yield"}
    elif yield_q < 25:
        return {"label": "Below Average", "color": "#f97316", "description": "Moderate improvements possible"}
    elif yield_q < 35:
        return {"label": "Average", "color": "#eab308", "description": "Near national average"}
    elif yield_q < 42:
        return {"label": "Good", "color": "#22c55e", "description": "Above average yield"}
    else:
        return {"label": "Excellent", "color": "#10b981", "description": "High-performance crop"}


def _get_recommendations(veg_stats, weather_agg, soil_norm, yield_pred) -> List[str]:
    recs = []
    ndvi = veg_stats.get("ndvi_mean", 0.4)
    precip = weather_agg.get("precip_total", 700)
    oc = soil_norm.get("organic_carbon", 1.0)
    ph = soil_norm.get("ph", 6.5)
    clay = soil_norm.get("clay", 28)

    if ndvi < 0.4:
        recs.append("⚠️ Low vegetation vigor — check for nutrient deficiency or pest stress")
    if ndvi > 0.75:
        recs.append("✅ Excellent canopy development — maintain current management practices")
    if precip < 500:
        recs.append("💧 Low rainfall — ensure supplemental irrigation during critical growth stages")
    if precip > 1500:
        recs.append("🌧️ High rainfall — monitor for flooding and fungal disease outbreaks")
    if oc < 0.8:
        recs.append("🌱 Low soil organic carbon — apply compost or green manure before next season")
    if ph < 5.5:
        recs.append("🧪 Acidic soil — apply lime to raise pH to 6.0–7.0 range")
    if ph > 7.5:
        recs.append("🧪 Alkaline soil — consider gypsum application and acidifying fertilizers")
    if clay > 50:
        recs.append("🏔️ Heavy clay soil — improve drainage to prevent waterlogging")
    if yield_pred < 20:
        recs.append("📈 Yield below potential — consider improved varieties (HYV) and precision fertilization")
    if not recs:
        recs.append("✅ Conditions look favorable — maintain water and nutrient management schedule")

    return recs[:4]


def _format_weather_summary(weather_agg: Dict) -> Dict:
    return {
        "avg_temperature_c": round(weather_agg.get("temp_mean", 28.0), 1),
        "total_rainfall_mm": round(weather_agg.get("precip_total", 800.0), 1),
        "rainy_days": int(weather_agg.get("precip_days", 60)),
        "avg_humidity_pct": round(weather_agg.get("humidity_mean", 72.0), 1),
        "solar_radiation_w_m2": round(weather_agg.get("solar_rad_mean", 18.5), 1),
    }
