import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer } from "../components/CommonComponents"; // ✅ Import missing components
import PropTypes from "prop-types"; // ✅ Import PropTypes

const RecentPapers = () => {
  const [papers, setPapers] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRecentPapers = async () => {
      try {
        const response = await api.get("/research/post_research_papers_others/");
        setPapers(response.data);
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          console.error("Error fetching recent papers:", error);
          alert("Error fetching recent papers.");
        }
      }
    };

    fetchRecentPapers();
  }, [navigate]);

  return (
    <FormContainer title="📄 Recent Research Papers">
      {papers.length > 0 ? (
        <ul className="space-y-4">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </ul>
      ) : (
        <p className="text-center text-gray-500">No recent papers available.</p>
      )}
    </FormContainer>
  );
};

// ✅ Paper Card Component
const PaperCard = ({ paper }) => {
  const [collabRequested, setCollabRequested] = useState(
    paper.can_request_collaboration !== undefined ? !paper.can_request_collaboration : false
  );

  const requestCollaboration = async (researchId) => {
    console.log("Requesting collaboration for Research ID:", researchId);

    if (!researchId || typeof researchId !== "number") {
      console.error("Invalid researchId:", researchId);
      alert("Error: Invalid research paper ID.");
      return;
    }

    try {
      const formData = new URLSearchParams();
      formData.append("message", "I would love to collaborate on this research.");

      const response = await api.post(`/research/request-collaboration/${researchId}/`, formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      if (response.status === 200) {
        alert("Collaboration request sent successfully!");
        setCollabRequested(true);
      } else {
        alert("Error: " + (response.data?.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Error requesting collaboration:", error);
      alert("Error requesting collaboration.");
    }
  };

  return (
    <li className="bg-white shadow-md rounded-lg p-6 flex justify-between items-center border border-gray-200">
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{paper.title}</h3>
        <p className="text-gray-700">
          <strong>Field:</strong> {paper.research_field}
        </p>
        <p className="text-gray-600">{paper.details}</p>
      </div>
      {!collabRequested ? (
        <button
          onClick={() => requestCollaboration(Number(paper.id))}
          className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-300"
        >
          Request Collaboration
        </button>
      ) : (
        <p className="text-green-600 font-semibold">Request Sent ✅</p>
      )}
    </li>
  );
};

// ✅ Add PropTypes for Validation
PaperCard.propTypes = {
  paper: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    research_field: PropTypes.string.isRequired,
    details: PropTypes.string.isRequired,
    can_request_collaboration: PropTypes.bool, // Optional
  }).isRequired,
};

export default RecentPapers;
