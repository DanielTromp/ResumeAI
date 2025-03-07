import axios from 'axios';

// For debugging network issues and direct API access
const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
console.log('Backend URL configured as:', backendUrl);

// Create a centralized axios instance for API calls
const api = axios.create({
  baseURL: backendUrl,
  timeout: 30000,
});

// Add a request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method.toUpperCase()} request to: ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`Response from ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
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