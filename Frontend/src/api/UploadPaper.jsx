import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, TextInput, SubmitButton } from "../components/CommonComponents";

const UploadPaper = () => {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [researchField, setResearchField] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false); // ✅ Handle loading state
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      alert("File size exceeds 5MB. Please select a smaller file.");
      return;
    }

    setFile(selectedFile);
  };

  const uploadPaper = async (e) => {
    e.preventDefault();

    if (!title || !author || !researchField || !file) {
      alert("Please fill all fields and select a file.");
      return;
    }

    setLoading(true); // ✅ Start loading
    const formData = new FormData();
    formData.append("title", title);
    formData.append("author", author);
    formData.append("research_field", researchField);
    formData.append("file", file);

    try {
      await api.post("/research/upload-paper/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert("Paper uploaded successfully!");
      setTitle("");
      setAuthor("");
      setResearchField("");
      setFile(null);
      navigate("/dashboard/research/my_post_research_papers"); // ✅ Redirect after upload
    } catch (error) {
      alert("Upload failed: " + JSON.stringify(error.response?.data || error.message));
    } finally {
      setLoading(false); // ✅ Stop loading
    }
  };

  return (
    <FormContainer title="Upload Research Paper">
      <form onSubmit={uploadPaper} className="space-y-4">
        <TextInput placeholder="Title" value={title} onChange={setTitle} />
        <TextInput placeholder="Author" value={author} onChange={setAuthor} />
        <TextInput placeholder="Research Field" value={researchField} onChange={setResearchField} />
        <input
          type="file"
          onChange={handleFileChange}
          required
          className="w-full border p-2 rounded mb-4"
        />
        <SubmitButton text={loading ? "Uploading..." : "Upload"} disabled={loading} />
      </form>
    </FormContainer>
  );
};



export default UploadPaper;