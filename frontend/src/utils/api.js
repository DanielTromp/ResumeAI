import axios from 'axios';

// For debugging network issues and direct API access
const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
console.log('Backend URL configured as:', backendUrl);
console.log('Window location:', window.location.href);
console.log('Current hostname:', window.location.hostname);

// Function to log API details to help diagnose issues
const logApiDetails = () => {
  // Get the Docker-related environment variables if available
  const dockerBackendUrl = process.env.REACT_APP_BACKEND_URL || 'Not set in env';
  const runtimeBackendUrl = backendUrl || 'Not set (empty string)';
  
  console.log('=== API CONFIGURATION DETAILS ===');
  console.log('API Base URL:', runtimeBackendUrl);
  console.log('REACT_APP_BACKEND_URL:', dockerBackendUrl);
  console.log('Window Origin:', window.location.origin);
  console.log('Running in Docker:', process.env.REACT_APP_RUNNING_IN_DOCKER || 'unknown');
  console.log('API Timeout:', '30000ms');
  console.log('================================');
};

// Log API details on initialization
logApiDetails();

// Create a centralized axios instance for API calls
const api = axios.create({
  baseURL: backendUrl,
  timeout: 30000,
  // Adding withCredentials if using cookies for auth
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    // Disable caching for all API requests
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});

// Add a request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    const fullUrl = `${config.baseURL || ''}${config.url}`;
    console.log(`🚀 Making ${config.method.toUpperCase()} request to: ${fullUrl}`);
    console.log('Request headers:', config.headers);
    
    if (config.data) {
      console.log('Request payload:', 
        typeof config.data === 'object' ? JSON.stringify(config.data).substring(0, 200) : 'non-JSON data');
    }
    
    if (config.params) {
      console.log('Request params:', config.params);
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request preparation error:', error.message);
    console.error('Error details:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    const fullUrl = `${response.config.baseURL || ''}${response.config.url}`;
    console.log(`✅ Response from ${fullUrl}:`, response.status);
    console.log('Response headers:', response.headers);
    
    // Log a preview of the response data
    if (response.data) {
      const dataPreview = typeof response.data === 'object' 
        ? JSON.stringify(response.data).substring(0, 200) + (JSON.stringify(response.data).length > 200 ? '...' : '')
        : 'non-JSON response';
      console.log('Response data preview:', dataPreview);
    }
    
    return response;
  },
  (error) => {
    console.error('❌ Response error:', error.message);
    
    // Network error (no response received)
    if (!error.response) {
      console.error('Network error - No response received');
      console.error('Request URL:', error.config ? `${error.config.baseURL || ''}${error.config.url}` : 'unknown');
      console.error('Request method:', error.config ? error.config.method.toUpperCase() : 'unknown');
      console.error('Is axios timeout?', error.code === 'ECONNABORTED');
      
      // Log more details about the browser environment
      console.error('Browser info:', navigator.userAgent);
      console.error('Online status:', navigator.onLine ? 'Online' : 'Offline');
      
      // Log connection details that might help diagnose the issue
      console.error('API Base URL:', api.defaults.baseURL);
      if (error.config && error.config.timeout) {
        console.error('Request timeout setting:', error.config.timeout + 'ms');
      }
    } 
    // Server responded with error status
    else {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
      console.error('Error headers:', error.response.headers);
    }
    
    return Promise.reject(error);
  }
);

// Vacancies API
export const getVacancies = (params = {}) => {
  return api.get('/api/vacancies', { params });
};

export const getVacancyById = (id) => {
  return api.get(`/api/vacancies/${id}`);
};

export const updateVacancy = (id, data) => {
  return api.put(`/api/vacancies/${id}`, data);
};

export const deleteVacancy = (id) => {
  return api.delete(`/api/vacancies/${id}`);
};

export const getVacancyStats = () => {
  return api.get('/api/statistics/vacancies');
};

export const rebuildVacancyStats = () => {
  return api.post('/api/statistics/vacancies/rebuild');
};

// Resumes API
export const getResumes = (params = {}) => {
  return api.get('/api/resumes', { params });
};

export const getResumeById = (id) => {
  return api.get(`/api/resumes/${id}`);
};

export default api;