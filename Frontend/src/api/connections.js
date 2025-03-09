import axios from "axios";

const API_URL = "http://127.0.0.1:8000/connections"; // Backend URL

// ✅ Get Auth Token from localStorage
const getAuthToken = () => localStorage.getItem("token");

// ✅ Fetch connections (Only for authenticated users)
export const getConnections = async () => {
  try {
    const response = await axios.get(`${API_URL}/connections`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch Connections Error:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Create a new connection (Only for authenticated users)
export const createConnection = async (friendId) => {
    try {
      const response = await axios.post(
        `${API_URL}/connect/`,
        { friend_id: Number(friendId) }, // ✅ Ensure friend_id is a number, not an object
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      return response.data;
    } catch (error) {
      console.error("Create Connection Error:", error.response?.data || error.message);
      throw error;
    }
  };
  

// ✅ Delete a connection (Only for authenticated users)
export const deleteConnection = async (connectionId) => {
  try {
    const response = await axios.delete(`${API_URL}/delete/${connectionId}/`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getAuthToken()}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Delete Connection Error:", error.response?.data || error.message);
    throw error;
  }
};