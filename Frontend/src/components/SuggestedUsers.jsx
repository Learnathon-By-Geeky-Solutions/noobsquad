import React, { useEffect, useState } from "react";
import axios from "axios";

const SuggestedUsers = () => {
  const [users, setUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({}); // Track status per user

  // Fetch users from the API
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get("http://127.0.0.1:8000/connections/users/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsers(response.data);

        // Initialize connectionStatus state for each user
        const initialStatus = {};
        response.data.forEach(user => {
          initialStatus[user.id] = "Connect";
        });
        setConnectionStatus(initialStatus);
      } catch (error) {
        console.error("Error fetching users:", error);
      }
    };

    fetchUsers();
  }, []);

  // Function to send connection request
  const sendConnectionRequest = async (userId) => {
    if (connectionStatus[userId] === "Pending") return; // Prevent duplicate requests

    setConnectionStatus(prevStatus => ({ ...prevStatus, [userId]: "Pending" })); // Optimistic UI update

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://127.0.0.1:8000/connections/connect/",
        { friend_id: userId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setConnectionStatus(prevStatus => ({ ...prevStatus, [userId]: "Pending" })); // Keep status pending
    } catch (error) {
      console.error("Error sending connection request:", error);
      setConnectionStatus(prevStatus => ({ ...prevStatus, [userId]: "Connect" })); // Revert on failure
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      <h2 className="text-xl font-semibold mb-4">People You May Know</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6">
        {users.map((user) => (
          <div key={user.id} className="bg-white shadow-md rounded-lg p-4 relative">
            
            {/* Close Button (X) in Top Right */}
            <button className="absolute top-2 right-2 bg-gray-200 rounded-full p-1 hover:bg-gray-300">
              ❌
            </button>

            {/* User Avatar */}
            <img
              src={user.avatar || "/default-avatar.png"}
              alt={user.username}
              className="w-20 h-20 rounded-full mx-auto"
            />

            {/* User Details */}
            <h3 className="text-lg font-bold text-center mt-2">{user.username}</h3>
            <p className="text-sm text-gray-500 text-center">{user.bio || "No bio available"}</p>

            {/* Mutual Connections */}
            <p className="text-xs text-gray-600 text-center mt-1">
              {user.mutualConnections || Math.floor(Math.random() * 50)} mutual connections
            </p>

            {/* Connect Button */}
            <button
              onClick={() => sendConnectionRequest(user.id)}
              disabled={connectionStatus[user.id] === "Pending"} // Disable if already pending
              className={`w-full ${
                connectionStatus[user.id] === "Pending" ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-700"
              } text-white font-bold py-2 px-4 rounded-lg mt-3 flex items-center justify-center`}
            >
              {connectionStatus[user.id] === "Pending" ? "Pending" : "➕ Connect"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SuggestedUsers;
