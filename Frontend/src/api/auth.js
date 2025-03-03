import axios from "axios";

const API_URL = "http://127.0.0.1:8000/auth"; // Backend URL

// ✅ Signup: Ensuring correct request format
export const signup = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/signup/`, {
      username: userData.username,
      email: userData.email,
      password: userData.password,  // ✅ Matches FastAPI schema
    }, {
      headers: { "Content-Type": "application/json" }, // ✅ Ensuring JSON format
    });

    return response.data;
  } catch (error) {
    console.error("Signup Error:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Login Function: Stores token after login
export const login = async (credentials) => {
  try {
    const formData = new URLSearchParams();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await axios.post(`${API_URL}/token`, formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    // ✅ Save the token in localStorage
    localStorage.setItem("token", response.data.access_token);

    return response.data;
  } catch (error) {
    console.error("Login Error:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Fetch User: Automatically includes token in headers
export const fetchUser = async () => {
  const token = localStorage.getItem("token"); // Retrieve stored token

  if (!token) {
    throw new Error("No authentication token found.");
  }

  return axios.get(`${API_URL}/users/me/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
};
