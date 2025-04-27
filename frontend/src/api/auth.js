import axios from 'axios';
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const signup = (data) => api.post('/auth/signup/', data);

export const login = (data) => {
  console.log("Login payload:", data.toString());
  return api.post('/auth/token', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};

export const fetchUser = () => api.get('/auth/users/me/');

export const verifyOtp = (data) => api.post('/auth/verify-otp/', data);

export const resendOtp = (data) => api.post('/auth/resend-otp/', data);

export const forgotPassword = (data) => {
  console.log("Forgot password payload:", data);
  return api.post('/auth/forgot-password/', data);
};

export const resetPassword = (data) => {
  console.log("Reset password payload:", data);
  return api.post('/auth/reset-password/', data);
};