import React, { useEffect, useState } from "react";
import axios from "axios";

const SuggestedUsers = () => {
  const [users, setUsers] = useState([]);
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});

  // Fetch users and incoming requests when the component mounts
  useEffect(() => {
    fetchUsers();
    fetchIncomingRequests();
  }, []);

  // ✅ Fetch users (People You May Know)
  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://127.0.0.1:8000/connections/users/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(response.data);

      // Initialize connectionStatus for each user
      const initialStatus = {};
      response.data.forEach(user => {
        initialStatus[user.id] = "Connect";
      });
      setConnectionStatus(initialStatus);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  // ✅ Fetch Incoming Connection Requests
  const fetchIncomingRequests = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://127.0.0.1:8000/connections/pending-requests", {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Fetch user details for each request
      const usersData = await Promise.all(
        response.data.map(async (req) => {
          try {
            const userResponse = await axios.get(`http://127.0.0.1:8000/connections/users/${req.user_id}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            return { ...req, userDetails: userResponse.data };
          } catch (error) {
            console.error("Error fetching user details:", error);
            return req; // Return request without user details
          }
        })
      );

      setIncomingRequests(usersData);
    } catch (error) {
      console.error("Error fetching incoming requests:", error);
    }
  };

  // ✅ Function to send a connection request
  const sendConnectionRequest = async (userId) => {
    if (connectionStatus[userId] === "Pending") return;

    setConnectionStatus(prevStatus => ({ ...prevStatus, [userId]: "Pending" }));

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://127.0.0.1:8000/connections/connect/",
        { friend_id: userId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error("Error sending connection request:", error);
      setConnectionStatus(prevStatus => ({ ...prevStatus, [userId]: "Connect" }));
    }
  };

  // ✅ Accept Connection Request
  const acceptConnectionRequest = async (requestId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `http://127.0.0.1:8000/connections/accept/${requestId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIncomingRequests(incomingRequests.filter(req => req.id !== requestId));
    } catch (error) {
      console.error("Error accepting request:", error);
    }
  };

  // ✅ Reject Connection Request
  const rejectConnectionRequest = async (requestId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `http://127.0.0.1:8000/connections/reject/${requestId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIncomingRequests(incomingRequests.filter(req => req.id !== requestId));
    } catch (error) {
      console.error("Error rejecting request:", error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Suggested Users */}
      <h2 className="text-xl font-semibold mb-4">People You May Know</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6">
        {users.map((user) => (
          <div key={user.id} className="bg-white shadow-md rounded-lg p-4 relative">
            {/* Close Button (X) */}
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

            {/* Connect Button */}
            <button
              onClick={() => sendConnectionRequest(user.id)}
              disabled={connectionStatus[user.id] === "Pending"}
              className={`w-full ${
                connectionStatus[user.id] === "Pending" ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-700"
              } text-white font-bold py-2 px-4 rounded-lg mt-3 flex items-center justify-center`}
            >
              {connectionStatus[user.id] === "Pending" ? "Pending" : "➕ Connect"}
            </button>
          </div>
        ))}
      </div>

      {/* Connection Requests */}
      <h2 className="text-xl font-semibold mt-8">Connection Requests</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-6">
        {incomingRequests.length > 0 ? (
          incomingRequests.map((req) => (
            <div key={req.id} className="bg-white shadow-md rounded-lg p-4 relative">
              {/* User Avatar */}
              <img
                src={req.userDetails?.avatar || "/default-avatar.png"}
                alt={req.userDetails?.username || "User"}
                className="w-20 h-20 rounded-full mx-auto"
              />

              {/* User Details */}
              <h3 className="text-lg font-bold text-center mt-2">
                {req.userDetails?.username || `User ${req.user_id}`} sent you a request
              </h3>
              <p className="text-sm text-gray-500 text-center">
                {req.userDetails?.bio || "No bio available"}
              </p>

              {/* Accept & Reject Buttons */}
              <div className="flex justify-between mt-3">
                <button
                  onClick={() => acceptConnectionRequest(req.id)}
                  className="w-1/2 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg mx-1"
                >
                  Accept
                </button>
                <button
                  onClick={() => rejectConnectionRequest(req.id)}
                  className="w-1/2 bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg mx-1"
                >
                  Reject
                </button>
              </div>
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500">No pending requests</p>
        )}
      </div>
    </div>
  );
};

export default SuggestedUsers;
