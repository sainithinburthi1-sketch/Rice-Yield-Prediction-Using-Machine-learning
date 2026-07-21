"""
ML Model Training Script
Trains a Multi-Layer Perceptron (MLPRegressor) for rice yield prediction.
scikit-learn's MLPRegressor provides full neural network functionality
and works on all Python versions (including 3.14+).

Generates a synthetic dataset calibrated to real Indian rice yield statistics.
Run automatically on first backend startup if no saved model is found.
Output: models/rice_yield_model.pkl + models/scaler.pkl
"""
import os
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "rice_yield_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")


def _generate_training_data(n_samples: int = 4000):
    """
    Generate synthetic training data that realistically represents
    rice yield variability across Indian agro-climatic zones.

    Yield range: 10–50 quintals/acre (100–500 kg per 0.01 ha)
    National average: ~26 q/acre (India 2023)
    Punjab average: ~40 q/acre (high-input irrigated)
    Assam/Odisha: ~14–18 q/acre (rainfed)
    """
    np.random.seed(42)

    X = []
    y = []

    for _ in range(n_samples):
        # ─── Vegetation Features ───────────────────────────────────
        ndvi_mean = np.clip(np.random.normal(0.55, 0.15), 0.1, 0.9)
        ndvi_max = np.clip(ndvi_mean + np.random.uniform(0.05, 0.2), 0.1, 0.95)
        ndvi_std = np.clip(np.random.normal(0.12, 0.04), 0.02, 0.35)
        evi_mean = np.clip(ndvi_mean * 0.82 + np.random.normal(0, 0.03), 0.05, 0.85)
        lswi_mean = np.clip(ndvi_mean * 0.55 - 0.05 + np.random.normal(0, 0.05), -0.3, 0.7)

        # ─── Weather Features ──────────────────────────────────────
        temp_mean = np.clip(np.random.normal(28.0, 3.5), 18.0, 38.0)
        temp_max = temp_mean + np.random.uniform(4, 8)
        temp_min = temp_mean - np.random.uniform(4, 8)
        precip_total = np.clip(np.random.normal(850, 250), 200, 2000)
        precip_days = int(np.clip(precip_total / 13, 15, 120))
        humidity_mean = np.clip(np.random.normal(72, 10), 40, 95)
        solar_rad_mean = np.clip(np.random.normal(18.5, 3.5), 8, 30)

        # ─── Soil Features ─────────────────────────────────────────
        clay = np.clip(np.random.normal(30, 10), 5, 65)
        sand = np.clip(np.random.normal(40, 12), 5, 80)
        silt = np.clip(100 - clay - sand, 5, 55)
        organic_carbon = np.clip(np.random.normal(1.2, 0.5), 0.1, 5.0)
        ph = np.clip(np.random.normal(6.5, 0.8), 4.5, 8.5)
        bulk_density = np.clip(np.random.normal(1.35, 0.15), 0.9, 1.8)

        # ─── Yield Simulation (domain-informed formula) ────────────
        # NDVI is the strongest predictor
        yield_ndvi = 30 * ndvi_mean + 5 * ndvi_max - 8 * ndvi_std

        # Water availability (monsoon 200–2000 mm range)
        precip_factor = (precip_total - 200) / 1800
        water_bonus = 8 * np.clip(precip_factor, 0, 1)

        # Temperature stress (rice optimal: 22–32°C)
        temp_stress = -abs(temp_mean - 27) * 0.5

        # Soil quality score
        soil_score = (organic_carbon * 2.5) + (0.2 * (ph - 5.5)) - (clay - 30) * 0.05
        soil_bonus = np.clip(soil_score, -3, 6)

        # Solar radiation (more photosynthetically active radiation → higher yield)
        solar_bonus = (solar_rad_mean - 15) * 0.3

        # Add realistic noise
        noise = np.random.normal(0, 2.0)
        final_yield = np.clip(yield_ndvi + water_bonus + temp_stress + soil_bonus + solar_bonus + noise, 8.0, 52.0)

        features = [
            ndvi_mean, ndvi_max, ndvi_std, evi_mean, lswi_mean,       # 5 vegetation
            temp_mean, temp_max, temp_min, precip_total, precip_days,  # 5 weather
            humidity_mean, solar_rad_mean,                             # 2 weather
            clay, sand, silt, organic_carbon, ph, bulk_density,        # 6 soil
        ]
        X.append(features)
        y.append(final_yield)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_and_save_model():
    """Train the MLP neural network and save to disk."""
    logger.info("Training rice yield neural network (MLPRegressor)...")

    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error

    X, y = _generate_training_data(n_samples=4000)

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_val, y_train, y_val = train_test_split(
        X_scaled, y, test_size=0.15, random_state=42
    )

    # ─── Neural Network Architecture ──────────────────────────────
    # 3 hidden layers: 256 → 128 → 64 neurons
    # ReLU activation, Adam optimizer, early stopping
    model = MLPRegressor(
        hidden_layer_sizes=(256, 128, 64, 32),
        activation="relu",
        solver="adam",
        alpha=0.001,            # L2 regularization
        batch_size=64,
        learning_rate="adaptive",
        learning_rate_init=0.001,
        max_iter=300,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=42,
        verbose=False,
    )

    model.fit(X_train, y_train)

    val_pred = model.predict(X_val)
    val_mae = mean_absolute_error(y_val, val_pred)
    logger.info(f"Model trained. Validation MAE: {val_mae:.2f} quintals/acre")

    # Save model and scaler
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    logger.info(f"Model saved → {MODEL_PATH}")
    logger.info(f"Scaler saved → {SCALER_PATH}")

    return model, scaler


def load_or_train_model():
    """Load existing model+scaler from disk, or train a new one."""
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            logger.info("Loaded existing model from disk.")
            return model, scaler
        except Exception as e:
            logger.warning(f"Failed to load saved model: {e}. Retraining...")

    return train_and_save_model()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    model, scaler = train_and_save_model()
    print("Training complete.")

    # Quick sanity check
    import numpy as np
    test_input = np.array([[0.65, 0.80, 0.10, 0.53, 0.30,
                            28.0, 35.0, 22.0, 900.0, 70,
                            72.0, 19.0,
                            32.0, 38.0, 30.0, 1.4, 6.5, 1.30]], dtype=np.float32)
    test_scaled = scaler.transform(test_input)
    pred = model.predict(test_scaled)
    print(f"Sample prediction (Punjab-like): {pred[0]:.1f} q/acre")
