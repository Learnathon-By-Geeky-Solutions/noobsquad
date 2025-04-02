import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import {
  Loader2,
  Handshake,
  UserCheck,
  XCircle,
  MessageCircle,
} from "lucide-react";
import dayjs from "dayjs";

const CollaborationRequests = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  // Fetch the collaboration requests
  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await api.get("/research/collaboration-requests/");
        if (response.data.length === 0) {
          setErrorMessage("No pending collaboration requests.");
        } else {
          setRequests(response.data);
        }
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          setErrorMessage("Error fetching collaboration requests.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRequests();
  }, [navigate]);

  // Handle accepting a collaboration request
  const handleAccept = async (id) => {
    try {
      await api.post(`/research/accept-collaboration/${id}/`);
      setRequests((prev) => prev.filter((req) => req.id !== id));
    } catch {
      alert("Failed to accept request. Please try again.");
    }
  };

  // Handle declining a collaboration request
  const handleDecline = async (id) => {
    try {
      await api.post(`/research/decline-collaboration/${id}/`);
      setRequests((prev) => prev.filter((req) => req.id !== id));
    } catch {
      alert("Failed to decline request. Please try again.");
    }
  };

  // Handle messaging a user
  const handleMessage = (username) => {
    alert(`Messaging ${username} (Coming soon...)`);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-blue-700 flex items-center gap-2 mb-6">
        <Handshake className="w-6 h-6" />
        Collaboration Requests
      </h2>

      {/* Loading State */}
      {loading && (
        <div data-testid="loader" className="flex justify-center mt-6">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      )}

      {/* Error Message */}
      {errorMessage && !loading && (
        <p className="text-center text-gray-500">{errorMessage}</p>
      )}

      {/* Collaboration Requests */}
      {!loading && !errorMessage && requests.length > 0 && (
        <ul className="space-y-4">
          {requests.map((req) => (
            <li
              key={req.id}
              className="flex flex-col sm:flex-row sm:justify-between items-start sm:items-center p-4 border rounded-md shadow-sm bg-gray-50 hover:bg-gray-100 transition"
            >
              {/* Sender Info */}
              <div className="flex items-start gap-4 w-full sm:w-3/4">
                <img
                  src={req.sender_avatar || "/default-avatar.png"}
                  alt="Avatar"
                  className="w-12 h-12 rounded-full object-cover border"
                />
                <div>
                  <h3 className="font-semibold text-gray-800">
                    {req.requester_username}
                  </h3>
                  <p className="text-sm text-gray-600">
                    wants to collaborate on{" "}
                    <span className="font-medium">{req.research_title}</span>
                  </p>
                  <p className="text-sm text-gray-500 mt-1">"{req.message}"</p>
                  {req.timestamp && (
                    <p className="text-xs text-gray-400 mt-1">
                      Sent {dayjs(req.timestamp).format("MMM D, YYYY h:mm A")}
                    </p>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 mt-4 sm:mt-0">
                <button
                  onClick={() => handleAccept(req.id)}
                  className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded-md hover:bg-green-700 transition text-sm"
                >
                  <UserCheck className="w-4 h-4" />
                  Accept
                </button>
                <button
                  onClick={() => handleMessage(req.requester_username)} // Pass the correct username
                  className="flex items-center gap-1 bg-gray-600 text-white px-3 py-1.5 rounded-md hover:bg-gray-700 transition text-sm"
                >
                  <MessageCircle className="w-4 h-4" />
                  Message
                </button>
                <button
                  onClick={() => handleDecline(req.id)}
                  className="flex items-center gap-1 bg-red-600 text-white px-3 py-1.5 rounded-md hover:bg-red-700 transition text-sm"
                >
                  <XCircle className="w-4 h-4" />
                  Decline
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* No requests found */}
      {!loading && !errorMessage && requests.length === 0 && (
        <p className="text-center text-gray-500">No collaboration requests found.</p>
      )}
    </div>
  );
};

export default CollaborationRequests;
