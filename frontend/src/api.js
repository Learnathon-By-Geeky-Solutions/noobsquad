import axios from "axios";

// Use environment variable in production, fallback to local development URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/';

// ✅ Create an Axios instance with JWT Authorization
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ Add an interceptor to include JWT token in every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token"); // Get JWT token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`; // Attach token
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ✅ Handle unauthorized requests (redirect to login)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      alert("Session expired! Please log in again.");
      localStorage.removeItem("token");
      window.location.href = "/login"; // Redirect to login
    }
    return Promise.reject(error);
  }
);

export default api;
