import React, { useState } from "react";
import api from "../api";
import { FormContainer, TextInput, SubmitButton, PaperCard} from "../components/CommonComponents";


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


export default SearchPapers;
