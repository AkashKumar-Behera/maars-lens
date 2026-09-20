import apiClient from './client';

export const listRulesApi = async (params = {}) => {
  // GET /api/v1/rules/?category=...&only_active=true&page=1&per_page=50
  const response = await apiClient.get('/rules/', { params });
  return response.data;
};

export const getRuleApi = async (ruleId) => {
  // GET /api/v1/rules/{ruleId}
  const response = await apiClient.get(`/rules/${ruleId}`);
  return response.data;
};

export const getRuleVersionApi = async (versionId) => {
  // GET /api/v1/rules/versions/{versionId}
  const response = await apiClient.get(`/rules/versions/${versionId}`);
  return response.data;
};

export const toggleRuleVersionActivationApi = async (versionId, isActive) => {
  // PATCH /api/v1/rules/versions/{versionId}/activate
  const response = await apiClient.patch(`/rules/versions/${versionId}/activate`, { is_active: isActive });
  return response.data;
};

export const getRuleAuditLogsApi = async (ruleId) => {
  // GET /api/v1/rules/{ruleId}/audit-logs
  const response = await apiClient.get(`/rules/${ruleId}/audit-logs`);
  return response.data;
};
