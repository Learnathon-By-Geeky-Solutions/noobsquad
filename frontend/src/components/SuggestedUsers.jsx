import React, { useEffect, useState } from "react";
import axios from "axios";
import ConnectedUsers from "../api/ConnectedUsers";
import { UserPlus, UserRoundPen, UserX, Loader2, UserCheck, Users, UserRoundCheck } from "lucide-react";
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
    <div className="max-w-7xl mx-auto p-4 mt-20 md:mt-24 space-y-8">
      {/* Incoming Requests Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <UserRoundCheck className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-800">Incoming Connection Requests</h2>
        </div>
        
        {loading.requests ? (
          <div className="flex justify-center items-center h-32">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : incomingRequests.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {incomingRequests.map((req) => (
              <div
                key={`request-${req.request_id}`}
                className="bg-gray-50 rounded-xl p-6 flex flex-col items-center text-center hover:shadow-md transition-shadow border border-gray-100"
              >
                <img
                  src={
                    req.profile_picture
                      ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${req.profile_picture}`
                      : "/default-avatar.png"
                  }
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover border-4 border-blue-100 mb-4"
                />

                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  {req.username || `User ${req.sender_id}`}
                </h3>

                <p className="text-gray-600 mb-4">
                  {req.email || "No email available"}
                </p>

                <div className="flex gap-3 w-full">
                  <button
                    onClick={() => acceptConnectionRequest(req.request_id)}
                    className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white py-2.5 px-4 rounded-lg font-medium transition shadow-sm"
                  >
                    <UserCheck className="w-5 h-5" />
                    Accept
                  </button>
                  <button
                    onClick={() => rejectConnectionRequest(req.request_id)}
                    className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white py-2.5 px-4 rounded-lg font-medium transition shadow-sm"
                  >
                    <UserX className="w-5 h-5" />
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No pending connection requests</p>
          </div>
        )}
      </div>

      {/* Suggested Users Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <UserPlus className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-800">People You May Know</h2>
        </div>

        {loading.users ? (
          <div className="flex justify-center items-center h-32">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Users className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No more people to connect with</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {users.map((user) => (
              <div 
                key={`user-${user.user_id}`} 
                className="bg-gray-50 rounded-xl p-6 flex flex-col items-center text-center hover:shadow-md transition-shadow border border-gray-100"
              >
                <img
                  src={
                    user.profile_picture
                      ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${user.profile_picture}`
                      : "/default-avatar.png"
                  }
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover border-4 border-blue-100 mb-4"
                />
                <h3 className="text-xl font-semibold text-gray-800 mb-1">
                  <UsernameLink username={user.username} />
                </h3>
                <p className="text-sm text-gray-500">{user.university_name || "University Name"}</p>
                        <p className="text-sm text-gray-500">{user.department || "Department Name"}</p>
                <button
                  onClick={() => sendConnectionRequest(user.user_id)}
                  disabled={connectionStatus[user.user_id] === "Pending"}
                  className={`w-full flex justify-center items-center gap-2 text-white font-medium py-2.5 px-4 rounded-lg transition shadow-sm ${
                    connectionStatus[user.user_id] === "Pending" 
                      ? "bg-gray-400 cursor-not-allowed" 
                      : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {connectionStatus[user.user_id] === "Pending" ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Pending
                    </>
                  ) : (
                    <>
                      <UserPlus className="w-5 h-5" />
                      Pair
                    </>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connected Users Section */}
      <div className="mt-8">
        <ConnectedUsers />
      </div>
    </div>
  );
};

export default SuggestedUsers;
