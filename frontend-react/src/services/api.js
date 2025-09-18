import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Patient API
export const patientAPI = {
  create: (patientData) => api.post('/patients/', patientData),
  get: (id) => api.get(`/patients/${id}`),
  list: (skip = 0, limit = 100) => api.get(`/patients?skip=${skip}&limit=${limit}`),
  updateVitals: (id, vitals) => api.put(`/patients/${id}/vitals`, vitals),
};

// Triage API
export const triageAPI = {
  assess: (patientId) => api.post('/triage/assess', { patient_id: patientId }),
  getQueue: () => api.get('/triage/queue'),
  getStatistics: () => api.get('/triage/statistics'),
  getAlerts: () => api.get('/alerts/active'),
  acknowledgeAlert: (alertId) => api.post(`/alerts/${alertId}/acknowledge`),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;