import React, { useEffect, useState } from "react";
import axios from "axios";
import ConnectedUsers from "../api/ConnectedUsers";
import { UserPlus, UserRoundPen, UserX, Loader2, UserCheck } from "lucide-react";
import UsernameLink from "./AboutMe/UsernameLink";

const SuggestedUsers = () => {
  const [users, setUsers] = useState([]);
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});
  const [loading, setLoading] = useState({
    users: true,
    requests: true
  });

  useEffect(() => {
    fetchUsers();
    fetchIncomingRequests();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/connections/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setUsers(response.data);
      const initialStatus = {};
      response.data.forEach(user => {
        initialStatus[user.user_id] = "Connect";
      });
      setConnectionStatus(initialStatus);
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(prev => ({ ...prev, users: false }));
    }
  };

  const fetchIncomingRequests = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/connections/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setIncomingRequests(response.data);
    } catch (error) {
      console.error("Error fetching incoming requests:", error);
    } finally {
      setLoading(prev => ({ ...prev, requests: false }));
    }
  };

  const sendConnectionRequest = async (userId) => {
    if (connectionStatus[userId] === "Pending") return;
    setConnectionStatus(prev => ({ ...prev, [userId]: "Pending" }));

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${import.meta.env.VITE_API_URL}/connections/connect/`,
        { friend_id: Number(userId) },
        { 
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          } 
        }
      );
    } catch (error) {
      console.error("Error sending connection request:", error);
      setConnectionStatus(prev => ({ ...prev, [userId]: "Connect" }));
    }
  };

  const acceptConnectionRequest = async (requestId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${import.meta.env.VITE_API_URL}/connections/accept/${requestId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIncomingRequests(prev => prev.filter(req => req.request_id !== requestId));
      // Refresh connections list
      fetchUsers();
    } catch (error) {
      console.error("Error accepting request:", error);
    }
  };

  const rejectConnectionRequest = async (requestId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${import.meta.env.VITE_API_URL}/connections/reject/${requestId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setIncomingRequests(prev => prev.filter(req => req.request_id !== requestId));
    } catch (error) {
      console.error("Error rejecting request:", error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 mt-20 md:mt-24">
      <h2 className="text-2xl font-bold flex items-center gap-2 mb-4 text-blue-700">
        <UserPlus className="w-6 h-6" /> People You May Know
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {loading.users ? (
          <p className="text-gray-500 col-span-full">Loading users...</p>
        ) : users.length === 0 ? (
          <p className="text-gray-500 col-span-full">No more people to connect with 🥺</p>
        ) : (
          users.map((user) => (
            <div key={`user-${user.user_id}`} className="bg-white shadow-md rounded-xl p-5">
              <img
                src={
                  user.profile_picture
                    ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${user.profile_picture}`
                    : "/default-avatar.png"
                }
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-2 border-blue-500 mb-3 mx-auto"
              />
              <h3 className="text-lg font-semibold text-center mt-3 text-gray-800">
                <UsernameLink username={user.username} />
              </h3>
              <p className="text-sm text-gray-500 text-center">{user.bio || "No bio available"}</p>
              <button
                onClick={() => sendConnectionRequest(user.user_id)}
                disabled={connectionStatus[user.user_id] === "Pending"}
                className={`w-full mt-4 flex justify-center items-center gap-2 text-white font-semibold py-2 px-4 rounded-md transition duration-200 ${
                  connectionStatus[user.user_id] === "Pending" ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {connectionStatus[user.user_id] === "Pending" ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Pending
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" /> Pair
                  </>
                )}
              </button>
            </div>
          ))
        )}
      </div>

      <h2 className="text-2xl font-bold mt-12 mb-4 flex items-center gap-2 text-blue-700">
        <UserRoundPen className="w-6 h-6" /> Incoming Connection Requests
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8 mt-8">
        {loading.requests ? (
          <p className="text-gray-500 col-span-full">Loading requests...</p>
        ) : incomingRequests.length > 0 ? (
          incomingRequests.map((req) => (
            <div
              key={`request-${req.request_id}`}
              className="bg-white rounded-xl shadow-md p-6 flex flex-col items-center text-center hover:shadow-lg transition-shadow"
            >
              <img
                src={
                  req.profile_picture
                    ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${req.profile_picture}`
                    : "/default-avatar.png"
                }
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-2 border-blue-500 mb-3 mx-auto"
              />

              <h3 className="text-lg font-semibold text-gray-800 mb-1">
                {req.username || `User ${req.sender_id}`}
              </h3>

              <p className="text-sm text-gray-500">
                {req.email || "No email available"}
              </p>

              <div className="flex gap-3 mt-4 w-full">
                <button
                  onClick={() => acceptConnectionRequest(req.request_id)}
                  className="flex-1 flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md font-medium transition"
                >
                  <UserCheck className="w-4 h-4" />
                  Accept
                </button>
                <button
                  onClick={() => rejectConnectionRequest(req.request_id)}
                  className="flex-1 flex items-center justify-center gap-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-md font-medium transition"
                >
                  <UserX className="w-4 h-4" />
                  Reject
                </button>
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-500 col-span-full text-center">No pending requests</p>
        )}
      </div>

      <div className="mt-12">
        <ConnectedUsers />
      </div>
    </div>
  );
};

export default SuggestedUsers;
