import React, { useEffect, useState, useContext } from "react";
import axios from "axios";
import { ChatContext } from "../context/ChatContext";

// Fetch single user details
const fetchUserDetails = async (userId) => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `http://127.0.0.1:8000/connections/user/${userId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching user details for ${userId}:`, error.message);
    return { id: userId, username: `User ${userId}`, avatar: "/default-avatar.png" };
  }
};

// Fetch all connected friends except the current user
const fetchConnectedUsers = async () => {
  try {
    const token = localStorage.getItem("token");
    const currentUserId = parseInt(localStorage.getItem("user_id"));

    const response = await axios.get(
      "http://127.0.0.1:8000/connections/connections/",
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (!Array.isArray(response.data)) {
      throw new Error("Unexpected API response format");
    }

    const friendIds = new Set();
    response.data.forEach((conn) => {
      if (conn.user_id === currentUserId) {
        friendIds.add(conn.friend_id);
      } else if (conn.friend_id === currentUserId) {
        friendIds.add(conn.user_id);
      }
    });

    const users = await Promise.all([...friendIds].map(fetchUserDetails));
    return users;
  } catch (error) {
    console.error("Error fetching connected users:", error.message);
    return [];
  }
};

const ConnectedUsers = () => {
  const [friends, setFriends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { openChat } = useContext(ChatContext);

  useEffect(() => {
    fetchConnectedUsers()
      .then(setFriends)
      .catch(() => setError("Failed to load friends. Please try again later."))
      .finally(() => setLoading(false));
  }, []);

  let content;

  if (loading) {
    content = <p className="text-gray-600">Loading...</p>;
  } else if (error) {
    content = <p className="text-red-500">{error}</p>;
  } else if (friends.length === 0) {
    content = (
      <p className="text-gray-600">
        No friends connected yet. Start connecting! 😊
      </p>
    );
  } else {
    content = (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6">
        {friends.map((friend) => (
          <div
            key={friend.id}
            className="bg-white shadow-md rounded-lg p-4 hover:shadow-lg transition-shadow"
          >
            <img
              src={friend.avatar || "/default-avatar.png"}
              alt={friend.username}
              className="w-20 h-20 rounded-full mx-auto border-2 border-gray-300"
            />
            <h3 className="text-lg font-bold text-center mt-2 text-gray-800">
              {friend.username}
            </h3>

            <button
              onClick={() => openChat(friend)}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 mt-3 rounded-lg"
            >
              💬 Message
            </button>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-100 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Your Friends</h2>
      {content}
    </div>
  );
};

export default ConnectedUsers;
