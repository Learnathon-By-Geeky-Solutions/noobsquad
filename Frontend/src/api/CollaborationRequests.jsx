import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import api from "../api";

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
        }
        setRequests(response.data);
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

  return (
    <FormContainer title="📜 Collaboration Requests">
      {loading ? (
        <p className="text-center text-gray-500">Loading requests...</p>
      ) : errorMessage ? (
        <p className="text-center text-gray-500">{errorMessage}</p>
      ) : (
        <ul className="space-y-4">
          {requests.map((req) => (
            <RequestCard key={req.id} req={req} />
          ))}
        </ul>
      )}
    </FormContainer>
  );
};

// ✅ Collaboration Request Card Component
const RequestCard = ({ req }) => (
  <li className="p-4 border rounded shadow-md bg-white">
    <strong className="text-gray-900">{req.requester_username}</strong> sent you a collaboration request
    <p className="text-gray-700">
      <strong>Message:</strong> {req.message}
    </p>
  </li>
);

// ✅ Reusable Components
const FormContainer = ({ title, children }) => (
  <div className="bg-white shadow-md rounded-lg p-6">
    <h2 className="text-xl font-semibold mb-4">{title}</h2>
    {children}
  </div>
);

// ✅ PropTypes Validation
FormContainer.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

RequestCard.propTypes = {
  req: PropTypes.shape({
    id: PropTypes.number.isRequired,
    requester_username: PropTypes.string.isRequired,
    message: PropTypes.string.isRequired,
  }).isRequired,
};

export default CollaborationRequests;
