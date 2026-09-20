import apiClient from './client';

// --- Customer Inquiries & Geo-Reporting ---
export const submitCustomerGeoReportApi = async (payload) => {
  const response = await apiClient.post('/inquiries/customer/geo-report', payload);
  return response.data;
};

export const listStoresApi = async () => {
  const response = await apiClient.get('/inquiries/stores');
  return response.data;
};

// --- Officer Incidents & Notice Dispatch ---
export const listOfficerIncidentsApi = async () => {
  const response = await apiClient.get('/inquiries/officer/incidents');
  return response.data;
};

export const sendOfficerInquiryApi = async (payload) => {
  const response = await apiClient.post('/inquiries/officer/send-inquiry', payload);
  return response.data;
};

export const escalateIncidentToAdminApi = async (reportId, reason) => {
  const formData = new FormData();
  formData.append('report_id', reportId);
  formData.append('reason', reason);
  const response = await apiClient.post('/inquiries/officer/escalate-to-admin', formData);
  return response.data;
};

// --- Retailer Inquiries & Traceability Proof ---
export const listRetailerInquiriesApi = async () => {
  const response = await apiClient.get('/inquiries/retailer/inquiries');
  return response.data;
};

export const submitSupplierProofApi = async (payload) => {
  const response = await apiClient.post('/inquiries/retailer/submit-supplier-proof', payload);
  return response.data;
};

// --- Admin National Geo-Intelligence & Legal Enforcement ---
export const getAdminGeoIntelligenceApi = async () => {
  const response = await apiClient.get('/inquiries/admin/geo-intelligence');
  return response.data;
};

export const executeAdminLegalActionApi = async (payload) => {
  const response = await apiClient.post('/inquiries/admin/legal-action', payload);
  return response.data;
};
