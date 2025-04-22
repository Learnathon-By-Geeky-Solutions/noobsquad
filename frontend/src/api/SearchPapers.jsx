import React, { useState, useEffect } from "react";
import api from "../api";
import ChatPopupWrapper from "../components/AIPopup";
import {
  Search,
  FileText,
  AlertTriangle,
  Loader2,
  Download,
  BookOpen,
  Bot,
} from "lucide-react";

const SearchPapers = () => {
  const [keyword, setKeyword] = useState("");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [error, setError] = useState("");
  const [showChat, setShowChat] = useState(false);
  const [fileToSend, setFileToSend] = useState(null);
  

  // ✅ Fetch all papers initially
  useEffect(() => {
    
    fetchAllPapers();
  }, []);

  const fetchAllPapers = async () => {
    setLoading(true);
    setErrorMessage("");
    try {
      const response = await api.get("/research/recommended/");
      setPapers(response.data);
    } catch (error) {
      console.error(error);
      setErrorMessage("Failed to load papers.");
    } finally {
      setLoading(false);
    }
  };

  // ✅ Search handler
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
      console.log("response:",response)
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

  // ✅ Download paper   
  const downloadPaper = async (paperId, originalFilename) => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("No token found. Please log in.");
      return;
    }
  
    const url = `/research/papers/download/${paperId}/`;
  
    try {
      const response = await api.get(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: "blob", // 🔥 this tells Axios to expect binary data
      });
  
      const blob = new Blob([response.data], { type: "application/pdf" });
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = originalFilename;
      console.log("originalFilename:",originalFilename)
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl); // Clean up
  
    } catch (err) {
      console.error("Download error:", err);
      setError("Failed to download paper.");
    }
  };


  const handleAskU = async (paper) => {
    try {
      console.log("inside paper:",paper)
      console.log("file_type_url:",paper.file_path)
      const response = await fetch(paper.file_path);
      const blob = await response.blob();
  
      const filename = paper.original_filename || "paper.pdf"; // fallback name
      const file = new File([blob], filename, { type: blob.type });
      console.log("file:",file)
  
      setFileToSend(file);
      setShowChat(true);
    } catch (err) {
      console.error("Failed to fetch file:", err);
    }
  };
  

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-4xl mx-auto">
      {/* Title */}
      <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 text-blue-700">
        <BookOpen className="w-6 h-6" />
        Research Papers
      </h2>

      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Search Papers by paper name, title, author (e.g. Elfred)"
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
                {paper.original_filename}
              </div>
              <p className="text-base text-gray-700">
                <span className="font-medium">Title:</span>{" "}
                {paper.title || "Unknown"}
              </p>
              <p className="text-sm text-gray-700">
                <span className="font-medium">Author:</span>{" "}
                {paper.author || "Unknown"}
              </p>
              <p className="text-sm text-gray-700">
                <span className="font-medium">Field:</span>{" "}
                {paper.research_field || "Unknown"}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {paper.abstract
                  ? paper.abstract.slice(0, 150) + "..."
                  : "No abstract available."}
              </p>

              {/* Download Button */}
              <div className="flex gap-3 mt-3">
              <button
                onClick={() => {
                  console.log("paper:", paper);
                  downloadPaper(paper.id, paper.original_filename);
                }}
                className="inline-flex items-center gap-2 text-sm bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 transition"
              >
                <Download className="w-4 h-4" />
                Download
              </button>

              <button
                onClick={() => {
                  console.log("paper:",paper)
                  handleAskU(paper)}}
                className="relative inline-flex items-center gap-2 text-sm font-medium text-white bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-500 px-4 py-2 rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-transform duration-200"
              >
                <Bot className="w-4 h-4 animate-pulse" />
                <span className="tracking-wide">AskU</span>

                {/* Online Indicator */}
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-green-400 rounded-full border-2 border-white animate-ping"></span>
              </button>

            </div>
            {showChat && (
              <ChatPopupWrapper
                onClose={() => setShowChat(false)}
                fileToSend={fileToSend} // 🔥 assuming paper.file is a `File` object or a blob
              />
            )}
            </li>
          ))}
        </ul>
      )}

      {/* Empty Message */}
      {!loading && papers.length === 0 && !errorMessage && (
        <p className="text-center text-gray-500 mt-6">
          No papers available yet. Start searching or upload a new one.
        </p>
      )}
    </div>
  );
};

export default SearchPapers;
