import React, { useEffect, useState, useContext } from "react";
import axios from "axios";
import { ChatContext } from "../context/ChatContext";
import { MessageCircle, UserCheck, Users, Loader2 } from "lucide-react";
import UsernameLink from "../components/AboutMe/UsernameLink";

const fetchUserDetails = async (userId) => {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL}/connections/user/${userId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  } catch (error) {
    console.error(`Error fetching user details for ${userId}:`, error.message);
    return { id: userId, username: `User ${userId}`, avatar: "/default-avatar.png" };
  }
};

const fetchConnectedUsers = async () => {
  const token = localStorage.getItem("token");
  const currentUserId = parseInt(localStorage.getItem("user_id"));
  const response = await axios.get(
    `${import.meta.env.VITE_API_URL}/connections/connections`,
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
};

const ConnectedUsers = () => {
  const [friends, setFriends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { openChat } = useContext(ChatContext);

  useEffect(() => {
    const fetchConnections = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/connections/connections`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (!Array.isArray(response.data)) {
          throw new Error("Unexpected API response format");
        }

        setFriends(response.data);
        setError(null);
      } catch (err) {
        console.error("Error fetching connections:", err);
        setError("Failed to load connections. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchConnections();
  }, []);

  const handleOpenChat = (friend) => {
    if (!friend || !friend.friend_id) {
      console.error("Invalid friend object:", friend);
      return;
    }
    openChat({
      id: friend.friend_id,
      username: friend.username,
      profile_picture: friend.profile_picture
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center gap-3 mb-6">
        <UserCheck className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-800">Your Connections</h2>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-32">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <div className="text-center py-12 bg-red-50 rounded-lg">
          <p className="text-red-600 text-lg">{error}</p>
        </div>
      ) : friends.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500 text-lg">You have no connections yet. Try pairing with someone!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {friends.map((friend) => (
            <div
              key={friend.connection_id}
              className="bg-gray-50 rounded-xl p-6 flex flex-col items-center text-center hover:shadow-md transition-shadow border border-gray-100"
            >
              <img
                src={
                  friend.profile_picture
                    ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${friend.profile_picture}`
                    : "/default-avatar.png"
                }
                alt="Profile"
                className="w-24 h-24 rounded-full object-cover border-4 border-blue-100 mb-4"
              />
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                <UsernameLink username={friend.username} />
              </h3>
              <p className="text-gray-600 mb-6">{friend.email || "No email available"}</p>
              <button
                onClick={() => handleOpenChat(friend)}
                className="w-full flex justify-center items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition shadow-sm"
              >
                <MessageCircle className="w-5 h-5" />
                Message
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConnectedUsers;