import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import PropTypes from "prop-types";
import { Loader2, FileText, Handshake, CheckCircle2 } from "lucide-react";

const RecentPapers = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
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
      } finally {
        setLoading(false);
      }
    };

    fetchRecentPapers();
  }, [navigate]);

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-blue-700 flex items-center gap-2 mb-6">
        <FileText className="w-6 h-6" />
        Recent Research Papers
      </h2>

      {(() => {
        if (loading) {
          return (
            <div className="flex justify-center mt-6">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          );
        }

        if (papers.length > 0) {
          return (
            <ul className="space-y-4">
              {papers.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
              ))}
            </ul>
          );
        }

        return <p className="text-center text-gray-500">No recent papers available.</p>;
      })()}
    </div>
  );
};

export const PaperCard = ({ paper }) => {
  const [collabRequested, setCollabRequested] = useState(
    paper.can_request_collaboration !== undefined ? !paper.can_request_collaboration : false
  );
  const [sending, setSending] = useState(false);

  const requestCollaboration = async (researchId) => {
    if (!researchId || typeof researchId !== "number") {
      alert("Invalid research paper ID.");
      return;
    }

    setSending(true);

    try {
      const formData = new URLSearchParams();
      formData.append("message", "I would love to collaborate on this research.");

      const response = await api.post(`/research/request-collaboration/${researchId}/`, formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      if (response.status === 200) {
        setCollabRequested(true);
        alert("Collaboration request sent successfully!");
      } else {
        alert("Error: " + (response.data?.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Error requesting collaboration:", error);
      alert("Error requesting collaboration.");
    } finally {
      setSending(false);
    }
  };

  return (
    <li className="bg-gray-50 border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow transition">
      <h3 className="text-lg font-semibold text-gray-800 mb-1"><strong>{paper.title}</strong></h3>
      <p className="text-sm text-gray-600 mb-1">
        <strong>Field:</strong> {paper.research_field}
      </p>
      <p className="text-sm text-gray-500 mb-4"><strong>Work details:</strong> {paper.details}</p>

      {!collabRequested ? (
        <button
          onClick={() => requestCollaboration(Number(paper.id))}
          disabled={sending}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
        >
          {sending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Handshake className="w-4 h-4" />
              Request Collaboration
            </>
          )}
        </button>
      ) : (
        <p className="flex items-center gap-1 text-green-600 font-medium">
          <CheckCircle2 className="w-5 h-5" />
          Request Sent
        </p>
      )}
    </li>
  );
};

PaperCard.propTypes = {
  paper: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    research_field: PropTypes.string.isRequired,
    details: PropTypes.string.isRequired,
    can_request_collaboration: PropTypes.bool,
  }).isRequired,
};

export default RecentPapers;
