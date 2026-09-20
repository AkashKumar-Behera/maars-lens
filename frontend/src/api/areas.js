import apiClient from './client';

export const listAreasApi = async () => {
  // GET /api/v1/areas/
  const response = await apiClient.get('/areas/');
  return response.data;
};
