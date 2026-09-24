import apiClient from './client';

export const loginApi = async (email, password) => {
  // Backend POST /api/v1/auth/login { email, password } -> { access_token, token_type }
  const response = await apiClient.post('/auth/login', { email, password });
  return response.data;
};

export const registerApi = async (data) => {
  // Backend POST /api/v1/auth/register with base & role-specific fields
  const response = await apiClient.post('/auth/register', data);
  return response.data;
};

export const registerCustomerApi = async (contact_channel) => {
  const response = await apiClient.post('/auth/register/customer', { contact_channel });
  return response.data;
};

export const getMeApi = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};
