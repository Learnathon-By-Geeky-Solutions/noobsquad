import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FilePlus, Loader2 } from "lucide-react"; // Assuming you are using Lucide icons

const UploadPaper = () => {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [researchField, setResearchField] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(""); // Error state to show error messages
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    console.log("Selected file:", selectedFile.name);

    // Ensure the file is not too large (Max: 5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("File size exceeds 5MB. Please select a smaller file.");
      setFile(null);
      return;
    }

    setError(""); // Reset error if file size is fine
    setFile(selectedFile);
  };

  const uploadPaper = async (e) => {
    e.preventDefault(); // Prevent default form submission

    if (!title || !author || !researchField || !file) {
      setError("Please fill all fields and select a file.");
      return;
    }

    setLoading(true);
    setError(""); // Reset any previous errors

    const formData = new FormData();
    formData.append("title", title);
    formData.append("author", author);
    formData.append("research_field", researchField);
    formData.append("file", file);

    try {
      const response = await api.post("/research/upload-paper/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert("Paper uploaded successfully!");

      // Reset form fields
      setTitle("");
      setAuthor("");
      setResearchField("");
      setFile(null);

      // Redirect to "My Research Papers"
      navigate("/dashboard/research/search");

      console.log("Uploaded File Path:", response.data.file_path); // Debugging
    } catch (error) {
      console.error("Upload Error:", error.response?.data || error.message);
      setError("Upload failed: " + (error.response?.data || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold flex items-center gap-2 text-blue-700 mb-6">
        <FilePlus className="w-6 h-6" />
        Upload Research Paper
      </h2>

      <form onSubmit={uploadPaper} className="space-y-4">
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <input
          type="text"
          placeholder="Author"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <input
          type="text"
          placeholder="Research Field"
          value={researchField}
          onChange={(e) => setResearchField(e.target.value)}
          className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* File Upload Section */}
        <div className="w-full">
          <label htmlFor="pdf-upload" className="block mb-1 text-sm font-medium text-gray-700">
            Upload PDF File (Max 5MB)
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            required
            id="pdf-upload"
            className="w-full p-2 border rounded-md file:mr-4 file:px-4 file:py-2 file:bg-blue-600 file:text-white file:rounded-md hover:file:bg-blue-700"
          />
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="flex items-center justify-center gap-2 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
    </div>
  );
};

export default UploadPaper;
