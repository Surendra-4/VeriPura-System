/Users/vaibhavithakur/veripura-system/frontend/src/api/services.js

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
