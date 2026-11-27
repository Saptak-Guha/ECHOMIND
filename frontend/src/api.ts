import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('echomind_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 means the token is gone or expired: drop it and send the user back to
// the sign-in screen rather than leaving every panel stuck on an error.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && localStorage.getItem('echomind_token')) {
      localStorage.removeItem('echomind_token');
      localStorage.removeItem('echomind_user');
      window.location.reload();
    }
    return Promise.reject(error);
  },
);

// ─── Auth ──────────────────────────────────────────────────────────────

export const authAPI = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
};

// ─── Ingestion ─────────────────────────────────────────────────────────

export const ingestionAPI = {
  uploadDocument: (data: { title: string; content: string; doc_type?: string }) =>
    api.post('/ingest/document', data),
  submitConversation: (messages: Array<{ role: string; content: string }>) =>
    api.post('/ingest/conversation', messages),
  batchUpload: (documents: Array<{ title: string; content: string; doc_type?: string }>) =>
    api.post('/ingest/batch', { documents }),
};

// ─── Twin ──────────────────────────────────────────────────────────────

export const twinAPI = {
  chat: (data: { message: string; conversation_id?: string }) =>
    api.post('/twin/chat', data),
  getProfile: () => api.get('/twin/profile'),
  getConversations: () => api.get('/twin/conversations'),
};

// ─── Memory ────────────────────────────────────────────────────────────

export const memoryAPI = {
  search: (query: string) => api.get(`/memory/search?query=${encodeURIComponent(query)}`),
  getTimeline: (limit = 50) => api.get(`/memory/timeline?limit=${limit}`),
  getStats: () => api.get('/memory/stats'),
  deleteMemory: (id: string) => api.delete(`/memory/${id}`),
};

// ─── Personality ───────────────────────────────────────────────────────

export const personalityAPI = {
  getProfile: () => api.get('/personality/profile'),
  getEvolution: () => api.get('/personality/evolution'),
};

// ─── Behavior ──────────────────────────────────────────────────────────

export const behaviorAPI = {
  getProfile: () => api.get('/behavior/profile'),
};

// ─── Prediction ────────────────────────────────────────────────────────

export const predictionAPI = {
  predict: (scenario: string) => api.post('/predict/decision', { scenario }),
  getHistory: () => api.get('/predict/history'),
};

// ─── Simulation ────────────────────────────────────────────────────────

export const simulationAPI = {
  simulate: (data: { simulation_type: string; title: string; params?: object }) =>
    api.post('/simulate/future', data),
  getHistory: () => api.get('/simulate/history'),
};

// ─── Knowledge Graph ───────────────────────────────────────────────────

export const graphAPI = {
  getVisualization: () => api.get('/graph/visualization'),
  search: (query: string) => api.get(`/graph/search?query=${encodeURIComponent(query)}`),
};

// ─── Analytics ─────────────────────────────────────────────────────────

export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getEmotions: () => api.get('/analytics/emotions'),
  getTimeline: () => api.get('/analytics/timeline'),
  getLLMStatus: () => api.get('/analytics/llm-status'),
};

export default api;
