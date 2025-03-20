import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, RequestCard } from "../components/CommonComponents";

const CollaborationRequests = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const response = await api.get("/research/collaboration-requests/");
        if (response.data.length === 0) {
          setErrorMessage("No pending requests.");
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

  const handleAccept = async (id) => {
    try {
      await api.post(`/research/accept-collaboration/${id}/`);
      setRequests((prevRequests) => prevRequests.filter((req) => req.id !== id));
    } catch (error) {
      alert("Failed to accept request. Please try again.");
    }
  };

  let content;
  if (loading) {
    content = <p className="text-center text-gray-500">Loading requests...</p>;
  } else if (errorMessage) {
    content = <p className="text-center text-gray-500">{errorMessage}</p>;
  } else {
    content = (
      <ul className="space-y-4">
        {requests.map((req) => (
          <div key={req.id} className="flex justify-between items-center p-4 border rounded-lg">
            <RequestCard req={req} />
            <button
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              onClick={() => handleAccept(req.id)}
            >
              Accept
            </button>
          </div>
        ))}
      </ul>
    );
  }

  return <FormContainer title="📜 Collaboration Requests">{content}</FormContainer>;
};

export default CollaborationRequests;
