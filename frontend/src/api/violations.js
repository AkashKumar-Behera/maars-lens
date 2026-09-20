import apiClient from './client';

export const getViolationApi = async (inspectionId) => {
  // GET /api/v1/violations/{inspectionId}
  const response = await apiClient.get(`/violations/${inspectionId}`);
  return response.data;
};

export const createViolationApi = async (inspectionId, payload) => {
  // POST /api/v1/violations/{inspectionId}
  // payload: { failing_rule_codes: [...], summary: "..." }
  const response = await apiClient.post(`/violations/${inspectionId}`, payload);
  return response.data;
};

export const updateViolationStatusApi = async (inspectionId, payload) => {
  // POST /api/v1/violations/{inspectionId}/status
  // payload: { status: "resolved"|"dismissed"|..., resolution_notes: "..." }
  const response = await apiClient.post(`/violations/${inspectionId}/status`, payload);
  return response.data;
};
