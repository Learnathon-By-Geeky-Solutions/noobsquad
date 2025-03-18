import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, PaperCard } from "../components/CommonComponents";


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


export default FetchUserPapers;
