import React, { useState } from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import api from "../api";

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

// ✅ Reusable Form Components
const FormContainer = ({ title, children }) => (
  <div className="bg-white shadow-md rounded-lg p-6">
    <h2 className="text-xl font-semibold mb-4">{title}</h2>
    {children}
  </div>
);

const TextInput = ({ placeholder, value, onChange }) => (
  <input
    type="text"
    placeholder={placeholder}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    required
    className="w-full border p-2 rounded"
  />
);

const SubmitButton = ({ text, disabled }) => (
  <button
    type="submit"
    className={`w-full text-white font-bold py-2 px-4 rounded ${
      disabled ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
    }`}
    disabled={disabled}
  >
    {text}
  </button>
);

// ✅ PropTypes Validation
FormContainer.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

TextInput.propTypes = {
  placeholder: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

SubmitButton.propTypes = {
  text: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
};

export default UploadPaper;