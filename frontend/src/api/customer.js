import apiClient from './client';

export const customerScanLabelApi = async (file, panelType = 'front') => {
  // POST /api/v1/customer/scan
  const formData = new FormData();
  formData.append('file', file);
  formData.append('panel_type', panelType);

  const response = await apiClient.post('/customer/scan', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const createCustomerReportApi = async (formData) => {
  // POST /api/v1/customer/reports
  const response = await apiClient.post('/customer/reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listCustomerReportsApi = async () => {
  // GET /api/v1/customer/reports
  const response = await apiClient.get('/customer/reports');
  return response.data;
};

export const getCustomerReportApi = async (reportId) => {
  // GET /api/v1/customer/reports/{reportId}
  const response = await apiClient.get(`/customer/reports/${reportId}`);
  return response.data;
};
