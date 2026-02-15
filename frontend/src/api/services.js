//Users/vaibhavithakur/veripura-system/frontend/src/api/services.js

import apiClient from './client';

/**
 * Upload a document for validation
 * @param {File} file - File object from input
 * @returns {Promise} Response with upload, validation, and verification data
 */
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/v1/upload', formData);

  return response.data;
};

/**
 * Get verification record by batch ID
 * @param {string} batchId - Batch identifier
 * @returns {Promise} Ledger record
 */
export const getVerificationRecord = async (batchId) => {
  const response = await apiClient.get(`/api/v1/verify/${batchId}`);
  return response.data;
};

/**
 * Get shipment consistency graph
 * @param {string} shipmentId - Shipment identifier
 * @returns {Promise} Graph with nodes and edges
 */
export const getShipmentConsistencyGraph = async (shipmentId) => {
  const response = await apiClient.get(`/api/v1/shipments/${shipmentId}/consistency-graph`);
  return response.data;
};

/**
 * Get QR code as base64
 * @param {string} batchId - Batch identifier
 * @returns {Promise} QR code data
 */
export const getQRCodeBase64 = async (batchId) => {
  const response = await apiClient.get(`/api/v1/qr/${batchId}/base64`);
  return response.data;
};

/**
 * Check ledger integrity
 * @returns {Promise} Integrity report
 */
export const checkLedgerIntegrity = async () => {
  const response = await apiClient.get('/api/v1/verify/integrity/check');
  return response.data;
};

/**
 * Health check
 * @returns {Promise} Health status
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Register local account
 * @param {{email: string, password: string}} payload
 * @returns {Promise}
 */
export const registerUser = async (payload) => {
  const response = await apiClient.post('/auth/register', payload);
  return response.data;
};

/**
 * Login with email/password
 * @param {{email: string, password: string}} payload
 * @returns {Promise<{access_token: string, token_type: string}>}
 */
export const loginUser = async (payload) => {
  const response = await apiClient.post('/auth/login', payload);
  return response.data;
};

/**
 * Fetch current authenticated user
 * @returns {Promise}
 */
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

/**
 * Fetch Google OAuth URL from backend
 * @returns {Promise<{authorization_url: string, state: string}>}
 */
export const getGoogleLoginUrl = async () => {
  const response = await apiClient.get('/auth/google/login');
  return response.data;
};

/**
 * Exchange Google authorization code for JWT
 * @param {string} code
 * @param {string | null} state
 * @returns {Promise<{access_token: string, token_type: string}>}
 */
export const googleCallbackLogin = async (code, state) => {
  const response = await apiClient.get('/auth/google/callback', {
    params: { code, state },
  });
  return response.data;
};
