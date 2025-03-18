import React, { useState } from "react";
import PropTypes from "prop-types";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { FormContainer, TextInput, TextArea, SubmitButton } from "../components/CommonComponents";

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

export default PostResearch;
