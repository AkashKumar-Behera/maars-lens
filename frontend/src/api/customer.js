import apiClient from './client';

export const customerScanLabelApi = async (filesOrFile, panelTypes = 'front') => {
  // POST /api/v1/customer/scan
  const formData = new FormData();
  if (Array.isArray(filesOrFile)) {
    filesOrFile.forEach((f) => {
      if (f) formData.append('files', f);
    });
    formData.append('panel_types', Array.isArray(panelTypes) ? JSON.stringify(panelTypes) : panelTypes);
  } else {
    formData.append('file', filesOrFile);
    formData.append('panel_type', panelTypes);
  }

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

export const submitRoleApplicationApi = async (payload) => {
  // POST /api/v1/customer/role-application
  const response = await apiClient.post('/customer/role-application', payload);
  return response.data;
};

export const getMyRoleApplicationApi = async () => {
  // GET /api/v1/customer/role-application/me
  const response = await apiClient.get('/customer/role-application/me');
  return response.data;
};

