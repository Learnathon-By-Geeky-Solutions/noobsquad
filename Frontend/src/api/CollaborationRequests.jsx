import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, RequestCard } from "../components/CommonComponents";

// ✅ Collaboration Requests Component
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

  // ✅ Extract Conditional Logic Before Return
  let content;
  if (loading) {
    content = <p className="text-center text-gray-500">Loading requests...</p>;
  } else if (errorMessage) {
    content = <p className="text-center text-gray-500">{errorMessage}</p>;
  } else {
    content = (
      <ul className="space-y-4">
        {requests.map((req) => (
          <RequestCard key={req.id} req={req} />
        ))}
      </ul>
    );
  }

  return <FormContainer title="📜 Collaboration Requests">{content}</FormContainer>;
};

export default CollaborationRequests;
