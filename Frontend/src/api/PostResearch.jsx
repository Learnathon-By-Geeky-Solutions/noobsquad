import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { Loader2, FilePlus, AlertTriangle } from "lucide-react";

const PostResearch = () => {
  const [title, setTitle] = useState("");
  const [researchField, setResearchField] = useState("");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const postResearch = async (e) => {
    e.preventDefault();

    if (!title.trim() || !researchField.trim() || !details.trim()) {
      setError("All fields are required.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("title", title);
    formData.append("research_field", researchField);
    formData.append("details", details);

    try {
      await api.post("/research/post-research/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert("✅ Research posted successfully!");
      setTitle("");
      setResearchField("");
      setDetails("");

      navigate("/dashboard/research/my_post_research_papers");
    } catch (error) {
      const errMsg = error.response?.data?.detail || "Error posting research. Please try again.";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold flex items-center gap-2 text-blue-700 mb-6">
        <FilePlus className="w-6 h-6" />
        Post Research for Collaboration
      </h2>

      <form onSubmit={postResearch} className="space-y-4">
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <input
          type="text"
          placeholder="Research Field"
          value={researchField}
          onChange={(e) => setResearchField(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <textarea
          placeholder="Details (describe the research project or idea)"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          rows={5}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 text-red-600 text-sm mt-1">
            <AlertTriangle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {loading ? "Posting..." : "Post Research"}
        </button>
      </form>
    </div>
  );
};

export default PostResearch;
