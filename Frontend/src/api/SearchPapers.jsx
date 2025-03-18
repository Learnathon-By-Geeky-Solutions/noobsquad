import React, { useState } from "react";
import PropTypes from "prop-types";
import api from "../api";

const SearchPapers = () => {
  const [keyword, setKeyword] = useState("");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const searchPapers = async () => {
    if (!keyword.trim()) {
      alert("Please enter a keyword.");
      return;
    }

    setLoading(true);
    setErrorMessage("");

    try {
      const response = await api.get(`/research/papers/search/?keyword=${keyword}`);
      if (response.data.length === 0) {
        setErrorMessage("No papers found.");
      }
      setPapers(response.data);
    } catch (error) {
      setErrorMessage("Error fetching papers. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <FormContainer title="🔎 Search Research Papers">
      <div className="flex gap-2">
        <TextInput placeholder="Enter keyword" value={keyword} onChange={setKeyword} />
        <SubmitButton text={loading ? "Searching..." : "Search"} onClick={searchPapers} disabled={loading} />
      </div>

      {errorMessage && <p className="text-red-500 text-center mt-2">{errorMessage}</p>}

      <ul className="mt-4 space-y-4">
        {papers.length > 0 ? (
          papers.map((paper) => <PaperCard key={paper.id} paper={paper} />)
        ) : (
          <p className="text-center text-gray-500">{errorMessage || "Start searching for research papers."}</p>
        )}
      </ul>
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

const SubmitButton = ({ text, onClick, disabled }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full text-white font-bold py-2 px-4 rounded ${
      disabled ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
    }`}
    disabled={disabled}
  >
    {text}
  </button>
);

const PaperCard = ({ paper }) => (
  <li className="p-4 border rounded shadow-md">
    <strong className="text-gray-900">{paper.title}</strong>
    <p className="text-gray-700">{paper.details}</p>
    <p className="text-gray-600">Author: {paper.author}</p>
  </li>
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
  onClick: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

PaperCard.propTypes = {
  paper: PropTypes.shape({
    title: PropTypes.string.isRequired,
    details: PropTypes.string.isRequired,
    author: PropTypes.string.isRequired,
  }).isRequired,
};

export default SearchPapers;
