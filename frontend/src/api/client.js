//Users/vaibhavithakur/veripura-system/frontend/src/api/client.js

import axios from 'axios';

const configuredBaseURL = import.meta.env.VITE_API_BASE_URL?.trim()?.replace(/\/+$/, '');
const baseURL = import.meta.env.DEV ? (configuredBaseURL || 'http://localhost:8000') : '';

// Create axios instance with default config.
// In production we intentionally use same-origin requests and rely on Vercel rewrites.
const apiClient = axios.create({
  baseURL,
  timeout: 300000, // 5 minutes (OCR + ML can be slow on free-tier cold starts)
});

// Request interceptor (for future auth tokens)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here when implemented
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor (global error handling)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request sent but no response
      console.error('Network Error:', error.message);
    } else {
      // Request setup error
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
