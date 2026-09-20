import apiClient from './client';

export const getProductHistoryApi = async (productId) => {
  // GET /api/v1/products/{product_id}/history
  const response = await apiClient.get(`/products/${productId}/history`);
  return response.data;
};
