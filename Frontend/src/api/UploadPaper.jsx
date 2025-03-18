import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, TextInput, SubmitButton } from "../components/CommonComponents";

const UploadPaper = () => {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [researchField, setResearchField] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    console.log("Selected file:", selectedFile.name);

    // ✅ Ensure the file is not too large (Max: 5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      alert("File size exceeds 5MB. Please select a smaller file.");
      return;
    }

    setFile(selectedFile);
  };

  const uploadPaper = async (e) => {
    e.preventDefault(); // ✅ Prevent default form submission

    if (!title || !author || !researchField || !file) {
      alert("Please fill all fields and select a file.");
      return;
    }

    setLoading(true);

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

      // ✅ Reset form fields
      setTitle("");
      setAuthor("");
      setResearchField("");
      setFile(null);

      // ✅ Redirect to "My Research Papers"
      navigate("/dashboard/research/my_post_research_papers");

      console.log("Uploaded File Path:", response.data.file_path); // ✅ Debugging
    } catch (error) {
      console.error("Upload Error:", error.response?.data || error.message);
      alert("Upload failed: " + JSON.stringify(error.response?.data || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <FormContainer title="Upload Research Paper">
      <form onSubmit={uploadPaper} className="space-y-4">
        <TextInput placeholder="Title" value={title} onChange={setTitle} />
        <TextInput placeholder="Author" value={author} onChange={setAuthor} />
        <TextInput placeholder="Research Field" value={researchField} onChange={setResearchField} />
        
        {/* ✅ File Upload */}
        <input
          type="file"
          onChange={handleFileChange}
          required
          className="w-full border p-2 rounded mb-4"
        />

        {/* ✅ Fixed Submit Button */}
        <SubmitButton text={loading ? "Uploading..." : "Upload"} disabled={loading} />
      </form>
    </FormContainer>
  );
};

export default UploadPaper;