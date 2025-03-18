import React, { useState } from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import api from "../api";

const PostResearch = () => {
  const [title, setTitle] = useState("");
  const [researchField, setResearchField] = useState("");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const postResearch = async (e) => {
    e.preventDefault();

    if (!title.trim() || !researchField.trim() || !details.trim()) {
      alert("All fields are required.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("title", title);
    formData.append("research_field", researchField);
    formData.append("details", details);

    try {
      await api.post("/research/post-research/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      alert("Research posted successfully!");
      setTitle("");
      setResearchField("");
      setDetails("");
      navigate("/dashboard/research/my_post_research_papers");
    } catch (error) {
      alert("Error posting research: " + JSON.stringify(error.response?.data || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <FormContainer title="📑 Post Research for Collaboration">
      <form onSubmit={postResearch} className="space-y-4">
        <TextInput placeholder="Title" value={title} onChange={setTitle} />
        <TextInput placeholder="Research Field" value={researchField} onChange={setResearchField} />
        <TextArea placeholder="Details" value={details} onChange={setDetails} />
        <SubmitButton text={loading ? "Posting..." : "Post"} disabled={loading} />
      </form>
    </FormContainer>
  );
};

// ✅ Reusable Components
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

const TextArea = ({ placeholder, value, onChange }) => (
  <textarea
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

TextArea.propTypes = {
  placeholder: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

SubmitButton.propTypes = {
  text: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
};

export default PostResearch;
