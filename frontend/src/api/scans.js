import apiClient from './client';

export const listScansApi = async () => {
  // GET /api/v1/scans/
  const response = await apiClient.get('/scans/');
  return response.data;
};

export const getScanResultApi = async (inspectionId) => {
  // GET /api/v1/scans/{id}/result
  const response = await apiClient.get(`/scans/${inspectionId}/result`);
  return response.data;
};

export const uploadScanApi = async (scanPayload) => {
  // POST /api/v1/scans/upload
  const response = await apiClient.post('/scans/upload', scanPayload);
  return response.data;
};

export const submitManualReviewApi = async (inspectionId, reviewPayload) => {
  // POST /api/v1/scans/{id}/result
  const response = await apiClient.post(`/scans/${inspectionId}/result`, reviewPayload);
  return response.data;
};

export const finalizeScanApi = async (inspectionId, finalizePayload) => {
  // POST /api/v1/scans/{id}/finalize
  const response = await apiClient.post(`/scans/${inspectionId}/finalize`, finalizePayload);
  return response.data;
};

export const uploadInspectionImagesApi = async (inspectionId, formData) => {
  // POST /api/v1/scans/{id}/images
  const response = await apiClient.post(`/scans/${inspectionId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listInspectionImagesApi = async (inspectionId) => {
  // GET /api/v1/scans/{id}/images
  const response = await apiClient.get(`/scans/${inspectionId}/images`);
  return response.data;
};

export const scanListingApi = async (payload) => {
  // POST /api/v1/scans/listing
  const response = await apiClient.post('/scans/listing', payload);
  return response.data;
};

