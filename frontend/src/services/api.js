/**
 * API Service Layer
 * All calls to the FastAPI backend.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes for ML inference + data fetching
});

/**
 * Run full yield prediction pipeline.
 * @param {Object} params - { latitude, longitude, start_date, end_date }
 */
export const predictYield = async (params) => {
  const response = await api.post('/predict', params);
  return response.data;
};

/**
 * Fetch vegetation index time series (NDVI, EVI, LSWI).
 */
export const getVegetationData = async (lat, lon, startDate, endDate) => {
  const response = await api.get('/vegetation', {
    params: { lat, lon, start_date: startDate, end_date: endDate },
  });
  return response.data;
};

/**
 * Fetch weather summary for location and date range.
 */
export const getWeatherData = async (lat, lon, startDate, endDate) => {
  const response = await api.get('/weather', {
    params: { lat, lon, start_date: startDate, end_date: endDate },
  });
  return response.data;
};

/**
 * Fetch soil properties for a location.
 */
export const getSoilData = async (lat, lon) => {
  const response = await api.get('/soil', {
    params: { lat, lon },
  });
  return response.data;
};

/**
 * Fetch example demo locations.
 */
export const getExampleLocations = async () => {
  const response = await api.get('/example-locations');
  return response.data.locations;
};

/**
 * Health check.
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
