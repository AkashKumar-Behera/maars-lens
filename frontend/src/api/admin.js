import apiClient from './client';

export const getAnalyticsOverviewApi = async () => {
  // GET /api/v1/admin/analytics/overview
  const response = await apiClient.get('/admin/analytics/overview');
  return response.data;
};

export const getAnalyticsTrendsApi = async (days = 7) => {
  // GET /api/v1/admin/analytics/trends?days=N
  const response = await apiClient.get('/admin/analytics/trends', { params: { days } });
  return response.data?.trends || response.data || [];
};

export const getExportCsvUrl = () => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  return `${baseURL}/admin/analytics/export`;
};

export const downloadExportCsvBlobApi = async () => {
  const response = await apiClient.get('/admin/analytics/export', {
    responseType: 'blob',
  });
  return response.data;
};

export const listUsersApi = async (params = {}) => {
  // GET /api/v1/admin/users
  const response = await apiClient.get('/admin/users', { params });
  return response.data;
};

export const toggleUserStatusApi = async (userId, isActive) => {
  // PATCH /api/v1/admin/users/{userId}/status
  const response = await apiClient.patch(`/admin/users/${userId}/status`, { is_active: isActive });
  return response.data;
};

export const listRoleApplicationsApi = async (status) => {
  // GET /api/v1/admin/role-applications
  const response = await apiClient.get('/admin/role-applications', {
    params: status ? { status } : {},
  });
  return response.data;
};

export const approveRoleApplicationApi = async (applicationId) => {
  // POST /api/v1/admin/role-applications/{applicationId}/approve
  const response = await apiClient.post(`/admin/role-applications/${applicationId}/approve`);
  return response.data;
};

export const rejectRoleApplicationApi = async (applicationId, remarks) => {
  // POST /api/v1/admin/role-applications/{applicationId}/reject
  const response = await apiClient.post(`/admin/role-applications/${applicationId}/reject`, {
    remarks,
  });
  return response.data;
};

export const changeUserRoleApi = async (userId, role) => {
  // PATCH /api/v1/admin/users/{userId}/role
  const response = await apiClient.patch(`/admin/users/${userId}/role`, { role });
  return response.data;
};

export const deleteUserApi = async (userId) => {
  // DELETE /api/v1/admin/users/{userId}
  const response = await apiClient.delete(`/admin/users/${userId}`);
  return response.data;
};
