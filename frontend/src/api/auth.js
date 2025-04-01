import api from "./axios"; // ✅ Import the centralized Axios instance

const API_URL = "/auth"; // No need for full URL, `axios.js` already has baseURL

export const signup = async (userData) => {
  return api.post(`${API_URL}/signup/`, userData);
};

export const login = async (credentials) => {
  try {
    const formData = new URLSearchParams();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await api.post(`${API_URL}/token`, formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    if (!response.data?.access_token) {
      throw new Error("No access_token received from backend");
    }

    localStorage.setItem("token", response.data.access_token);
    return response.data; // ✅ Explicitly return the response data
  } catch (error) {
    console.error("Login error:", error.response?.data || error.message);
    throw error;
  }
};

export const fetchUser = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const response = await api.get(`${API_URL}/users/me/`, {
      headers: { Authorization: `Bearer ${token}` }, // ✅ Ensure token is included
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching user:", error.response?.data || error.message);
    throw error;
  }
};
