import React, { useEffect, useState, useContext } from "react";
import axios from "axios";
import { ChatContext } from "../context/ChatContext";
import { MessageCircle, UserCheck } from "lucide-react";

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

const fetchConnectedUsers = async () => {
  try {
    const token = localStorage.getItem("token");
    const currentUserId = parseInt(localStorage.getItem("user_id"));
    const response = await axios.get(
      "http://127.0.0.1:8000/connections/connections/",
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

  const renderContent = () => {
    if (loading) {
      return <p className="text-gray-500">Loading your connections...</p>;
    } else if (error) {
      return <p className="text-red-500">{error}</p>;
    } else if (friends.length === 0) {
      return <p className="text-gray-500">You have no connections yet. Try pairing with someone!</p>;
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8 mt-6">
        {friends.map((friend) => (
          <div
            key={friend.id}
            className="bg-white shadow-md rounded-xl p-6 flex flex-col items-center text-center hover:shadow-lg transition"
          >
            <img       
          src={
            friend.profile_picture
                  ? `http://127.0.0.1:8000/uploads/profile_pictures/${friend.profile_picture}`
                  : "/default-avatar.png"
            }
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-2 border-blue-500 mb-3 mx-auto"
             />
            <h3 className="text-lg font-semibold text-gray-800">{friend.username}</h3>

            <button
              onClick={() => openChat(friend)}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium flex items-center justify-center gap-2 transition"
            >
              <MessageCircle className="w-4 h-4" />
              Message
            </button>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4">
      <h2 className="text-2xl font-bold mt-12 mb-4 flex items-center gap-2 text-blue-700">
        <UserCheck className="w-6 h-6" />
        Your Connections
      </h2>

      {renderContent()}
    </div>
  );
};

export default ConnectedUsers;
