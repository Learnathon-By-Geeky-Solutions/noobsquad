import React, { useEffect, useState } from "react";
import api from "../../api";
import { FileText, AlertTriangle, Download, Bot } from "lucide-react";
import ChatPopupWrapper from "../AIPopup";
import axios from "axios";

const UserPapers = ({ userId }) => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [showChat, setShowChat] = useState(false);
  const [fileToSend, setFileToSend] = useState(null);

  useEffect(() => {
    console.log("Fetching papers for userId:", userId);
    fetchUserPapers();
  }, [userId]);

  const fetchUserPapers = async () => {
    try {
      const response = await api.get(`/research/papers/user/${userId}/`);
      console.log("response:", response.data);
      setPapers(response.data);
    } catch (err) {
      console.error(err);
      setErrorMessage("Failed to load user papers.");
    } finally {
      setLoading(false);
    }
  };

  const downloadPaper = async (paperId, filename) => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please log in to download papers.");
      return;
    }

    try {
      const response = await api.get(`/research/papers/download/${paperId}/`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });

      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download error:", err);
    }
  };

  const handleAskU = async (paper) => {
    try {
      const response = await fetch(paper.file_path);
      const blob = await response.blob();
      const file = new File([blob], paper.original_filename, { type: blob.type });
      setFileToSend(file);
      setShowChat(true);
    } catch (err) {
      console.error("AskU fetch error:", err);
    }
  };

  if (loading) return <p className="text-gray-600">Loading...</p>;
  if (errorMessage) return <p className="text-red-600">{errorMessage}</p>;

  return (
    <div className="space-y-4 mt-6">
      {papers.map((paper) => (
        <div key={paper.id} className="p-4 border mt-30 rounded bg-gray-50 shadow-sm">
          <h3 className="font-semibold text-blue-800 flex items-center gap-2 max-w-full break-words whitespace-pre-wrap break-all">
  <FileText className="w-4 h-4 shrink-0" />
  <span className="break-words break-all whitespace-pre-wrap">{paper.original_filename}</span>
          </h3>
          <p><strong>Title:</strong> {paper.title}</p>
          <p><strong>Author:</strong> {paper.author}</p>
          <p><strong>Field:</strong> {paper.research_field}</p>
          <p className="text-sm text-gray-600 mt-1">
            {paper.abstract ? `${paper.abstract.slice(0, 150)}...` : "No abstract."}
          </p>

          <div className="flex gap-3 mt-3">
            <button
              className="bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700"
              onClick={() => downloadPaper(paper.id, paper.original_filename)}
            >
              <Download className="w-4 h-4 inline mr-1" />
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
        </div>
      ))}
      {showChat && (
        <ChatPopupWrapper fileToSend={fileToSend} onClose={() => setShowChat(false)} />
      )}
    </div>
  );
};

export default UserPapers;
