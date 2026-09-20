import apiClient from './client';

export const loginApi = async (email, password) => {
  // Backend POST /api/v1/auth/login { email, password } -> { access_token, token_type }
  const response = await apiClient.post('/auth/login', { email, password });
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
