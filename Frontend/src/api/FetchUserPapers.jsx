import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import api from "../api";

const FetchUserPapers = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserPapers = async () => {
      try {
        const response = await api.get("/research/my_post_research_papers/");
        if (response.data.length === 0) {
          setErrorMessage("No research papers found.");
        }
        setPapers(response.data);
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          setErrorMessage("Error fetching research papers.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUserPapers();
  }, [navigate]);

  return (
    <FormContainer title="📑 My Research Papers">
      {loading ? (
        <p className="text-center text-gray-500">Loading research papers...</p>
      ) : errorMessage ? (
        <p className="text-center text-gray-500">{errorMessage}</p>
      ) : (
        <ul className="space-y-4">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </ul>
      )}
    </FormContainer>
  );
};

// ✅ Paper Card Component
const PaperCard = ({ paper }) => (
  <li className="p-4 border rounded shadow-md bg-white">
    <h3 className="text-lg font-semibold text-gray-900">{paper.title}</h3>
    <p className="text-gray-700"><strong>Field:</strong> {paper.research_field}</p>
    <p className="text-gray-600">{paper.details}</p>
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

PaperCard.propTypes = {
  paper: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    research_field: PropTypes.string.isRequired,
    details: PropTypes.string.isRequired,
  }).isRequired,
};

export default FetchUserPapers;
