import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { Loader2, FileText } from "lucide-react";

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
        } else {
          setPapers(response.data);
        }
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          setErrorMessage("Error fetching your research papers.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUserPapers();
  }, [navigate]);

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-blue-700 flex items-center gap-2 mb-6">
        <FileText className="w-6 h-6" />
        My current works (Ongoing)
      </h2>

      {loading && (
        <div className="flex justify-center mt-6">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      )}

      {!loading && errorMessage && (
        <p className="text-center text-gray-500">{errorMessage}</p>
      )}

      {!loading && !errorMessage && (
        <ul className="space-y-4">
          {papers.map((paper) => (
            <li
              key={paper.id}
              className="p-4 border border-gray-200 bg-gray-50 rounded-lg shadow-sm hover:bg-gray-100 transition"
            >
              <h3 className="text-lg font-semibold text-gray-800">{paper.title}</h3>
              <p className="text-sm text-gray-600">
                <strong>Field:</strong> {paper.research_field}
              </p>
              <p className="text-sm text-gray-500 mt-1"><strong>Details:</strong> {paper.details}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FetchUserPapers;
