import React, { useState } from "react";
import api from "../api";
import { Search, FileText, AlertTriangle, Loader2 } from "lucide-react";

const SearchPapers = () => {
  const [keyword, setKeyword] = useState("");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const searchPapers = async () => {
    if (!keyword.trim()) {
      setErrorMessage("Please enter a keyword to search.");
      return;
    }

    setLoading(true);
    setErrorMessage("");
    setPapers([]);

    try {
      const response = await api.get(`/research/papers/search/?keyword=${keyword}`);
      if (response.data.length === 0) {
        setErrorMessage("No papers found.");
      } else {
        setPapers(response.data);
      }
    } catch (error) {
      console.error(error);
      setErrorMessage("Error fetching papers. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      {/* Title */}
      <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 text-blue-700">
        <Search className="w-6 h-6" />
        Search Research Papers
      </h2>

      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Enter keyword (e.g. AI, robotics, healthcare)"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="flex-grow px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={searchPapers}
          disabled={loading}
          className="flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="flex items-center gap-2 text-red-600 mt-4">
          <AlertTriangle className="w-5 h-5" />
          <p>{errorMessage}</p>
        </div>
      )}

      {/* Results */}
      {papers.length > 0 && (
        <ul className="mt-6 space-y-4">
          {papers.map((paper) => (
            <li
              key={paper.id}
              className="p-4 border rounded-lg bg-gray-50 hover:bg-gray-100 transition shadow-sm"
            >
              <div className="flex items-center gap-2 text-blue-800 font-semibold mb-1">
                <FileText className="w-5 h-5" />
                {paper.title}
              </div>
              <p className="text-sm text-gray-700">
                <span className="font-medium">Author:</span>{" "}
                {paper.author || "Unknown"}
              </p>
              <p className="text-sm text-gray-700">
                <span className="font-medium">Field:</span>{" "}
                {paper.research_field || "Unknown"}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {paper.abstract ? paper.abstract.slice(0, 150) + "..." : "No abstract available."}
              </p>
            </li>
          ))}
        </ul>
      )}

      {/* Empty message (only if no error and not loading) */}
      {!loading && papers.length === 0 && !errorMessage && (
        <p className="text-center text-gray-500 mt-6">
          Start searching to view research papers.
        </p>
      )}
    </div>
  );
};

export default SearchPapers;
