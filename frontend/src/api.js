import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

export const getHealth = () => api.get('/health');
export const getModels = () => api.get('/models');
export const selectModel = (model) => api.post('/models/select', { model });

export const getProjects = () => api.get('/projects');
export const createProject = (data) => api.post('/projects', data);
export const getProject = (id) => api.get(`/projects/${id}`);
export const deleteProject = (id) => api.delete(`/projects/${id}`);

export const getVersions = (projectId) => api.get(`/versions/${projectId}`);
export const rollbackVersion = (projectId, versionNumber) =>
  api.post(`/versions/${projectId}/rollback`, { version_number: versionNumber });

export const startWorkflow = (data) => api.post('/workflow/start', data);
export const getWorkflow = (taskId) => api.get(`/workflow/${taskId}`);

export const generateCode = (data) => api.post('/generate', data);
export const debugCode = (data) => api.post('/debug', data);
export const reviewCode = (data) => api.post('/review', data);
export const testCode = (data) => api.post('/test', data);
export const executeCode = (data) => api.post('/execute', data);
export const getExecutionStatus = () => api.get('/execute/status');

export const getGovernance = (taskId) => api.get(`/governance/${taskId}`);
export const submitApproval = (taskId, approved, reason) =>
  api.post(`/approvals/${taskId}`, { approved, reason });
export const getHistory = () => api.get('/history');
export const getStats = () => api.get('/stats');

export default api;
