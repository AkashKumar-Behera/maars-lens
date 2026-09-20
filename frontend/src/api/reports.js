import apiClient from './client';

export const getReportSummaryApi = async (inspectionId) => {
  // GET /api/v1/reports/{inspectionId}/summary
  const response = await apiClient.get(`/reports/${inspectionId}/summary`);
  return response.data;
};

export const verifyReportApi = async (inspectionId) => {
  // GET /api/v1/reports/{inspectionId}/verify
  const response = await apiClient.get(`/reports/${inspectionId}/verify`);
  return response.data;
};

export const downloadReportPdfUrl = (inspectionId) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  return `${baseURL}/reports/${inspectionId}/pdf`;
};

export const downloadReportPdfBlobApi = async (inspectionId) => {
  const response = await apiClient.get(`/reports/${inspectionId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadReportDocxBlobApi = async (inspectionId) => {
  const response = await apiClient.get(`/reports/${inspectionId}/docx`, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadReportXlsxBlobApi = async (inspectionId) => {
  const response = await apiClient.get(`/reports/${inspectionId}/xlsx`, {
    responseType: 'blob',
  });
  return response.data;
};

