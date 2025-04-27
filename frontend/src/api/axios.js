import axios from "axios";

// ✅ Base API URL
const API_URL = import.meta.env.VITE_API_URL.replace('http', 'https');

// ✅ Create an Axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ✅ Attach Token to Requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// ✅ Global Error Handling
api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    console.error("Unauthorized! Redirecting to login...");
    localStorage.removeItem("token");
    window.location.href = "/login"; // Redirect user
  }
  return Promise.reject(error);
});

export default api;
