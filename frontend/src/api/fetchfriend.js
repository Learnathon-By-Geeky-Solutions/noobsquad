import axios from "axios";

export const fetchUserDetails = async (userId) => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL}/connections/user/${userId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching user details for ${userId}:`, error.message);
    return { id: userId, username: `User ${userId}`, profile_picture: null };
  }
};

export const fetchConnectedUsers = async () => {
  try {
    const token = localStorage.getItem("token");
    const currentUserId = parseInt(localStorage.getItem("user_id"));
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL}/connections/connections/`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (!Array.isArray(response.data)) throw new Error("Unexpected API response format");

    const friendIds = new Set();
    response.data.forEach((conn) => {
      if (conn.user_id === currentUserId) friendIds.add(conn.friend_id);
      else if (conn.friend_id === currentUserId) friendIds.add(conn.user_id);
    });

    const users = await Promise.all([...friendIds].map(fetchUserDetails));
    return users;
  } catch (error) {
    console.error("Error fetching connected users:", error.message);
    return [];
  }
};
