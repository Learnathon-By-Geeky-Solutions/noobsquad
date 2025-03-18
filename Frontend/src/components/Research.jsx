import React, { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate } from "react-router-dom";
import api from "../api"; // ✅ Import the API instance
import RecentPapers from "../api/RecentPapers";

const Research = () => {
  return (
    <div>
       {/* ✅ Use Absolute Paths to Avoid Nested Navigation Issues */}
        <nav className="p-4 bg-gray-200 flex justify-around">
            <Link to="/dashboard/research/search">🔎 Search Papers</Link>
            <Link to="/dashboard/research/upload">📤 Upload Paper</Link>
            <Link to="/dashboard/research/post-research">📑 Post Research</Link>
            <Link to="/dashboard/research/recent-works">📑 Recent Works</Link>
            <Link to="/dashboard/research/collab-requests">📜 Collaboration Requests</Link>
            <Link to="/dashboard/research/my_post_research_papers">📜 Currently working</Link>

        </nav>

      {/* Research Nested Routes */}
      <div className="max-w-6xl mx-auto p-6">
        <Routes>
          <Route path="search" element={<SearchPapers />} />
          <Route path="upload" element={<UploadPaper />} />
          <Route path="post-research" element={<PostResearch />} />
          <Route path="recent-works" element={<RecentPapers />} />
          <Route path="collab-requests" element={<CollaborationRequests />} />
          <Route path="my_post_research_papers" element={<FetchUserPapers />} />
        </Routes>
      </div>
    </div>
  );
};

// ✅ Upload Research Paper Component
const UploadPaper = () => {
    const [title, setTitle] = useState("");
    const [author, setAuthor] = useState("");
    const [researchField, setResearchField] = useState("");
    const [file, setFile] = useState(null);
    const navigate = useNavigate();
  
    const uploadPaper = async (e) => {
      e.preventDefault();
  
      // ✅ Check if all fields are filled
      if (!title || !author || !researchField || !file) {
        alert("Please fill all fields and select a file.");
        return;
      }
  
      const formData = new FormData();
      formData.append("title", title);
      formData.append("author", author);
      formData.append("research_field", researchField);
      formData.append("file", file);
  
      try {
        const response = await api.post("/research/upload-paper/", formData, {
          headers: {
            "Content-Type": "multipart/form-data", // ✅ Ensure correct content type
          },
        });
  
        alert("Paper uploaded successfully!");
        setTitle("");
        setAuthor("");
        setResearchField("");
        setFile(null);
      } catch (error) {
        if (error.response) {
          console.error("Upload Error:", error.response.data);
          alert("Upload failed: " + JSON.stringify(error.response.data));
        } else {
          alert("An error occurred while uploading.");
        }
      }
    };
  
    return (
      <FormContainer title="Upload Research Paper">
        <form onSubmit={uploadPaper}>
          <TextInput placeholder="Title" value={title} onChange={setTitle} />
          <TextInput placeholder="Author" value={author} onChange={setAuthor} />
          <TextInput placeholder="Research Field" value={researchField} onChange={setResearchField} />
          <input type="file" onChange={(e) => setFile(e.target.files[0])} required className="mb-4" />
          <SubmitButton text="Upload" />
        </form>
      </FormContainer>
    );
  };
  

// ✅ Search Research Papers Component
const SearchPapers = () => {
  const [keyword, setKeyword] = useState("");
  const [papers, setPapers] = useState([]);

  const searchPapers = async () => {
    try {
      const response = await api.get(`/research/papers/search/?keyword=${keyword}`);
      setPapers(response.data);
    } catch (error) {
      alert("No papers found.");
    }
  };

  return (
    <FormContainer title="Search Research Papers">
      <div className="flex gap-2">
        <TextInput placeholder="Enter keyword" value={keyword} onChange={setKeyword} />
        <SubmitButton text="Search" onClick={searchPapers} />
      </div>
      <ul className="mt-4">
        {papers.map((paper) => (
          <PaperCard key={paper.id} paper={paper} />
        ))}
      </ul>
    </FormContainer>
  );
};

// ✅ Handle JWT for Other API Requests
const PostResearch = () => {
    const [title, setTitle] = useState("");
    const [researchField, setResearchField] = useState("");
    const [details, setDetails] = useState("");
    const navigate = useNavigate();
  
    const postResearch = async (e) => {
      e.preventDefault();
  
      if (!title || !researchField || !details) {
        alert("All fields are required.");
        return;
      }
  
      // ✅ Create FormData (because FastAPI expects form data)
      const formData = new FormData();
      formData.append("title", title);
      formData.append("research_field", researchField);
      formData.append("details", details);
  
      try {
        // ✅ Ensure the request is sent as `multipart/form-data`
        const response = await api.post("/research/post-research/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
  
        alert("Research posted successfully!");
        setTitle("");
        setResearchField("");
        setDetails("");
      } catch (error) {
        if (error.response) {
          console.error("Post Research Error:", error.response.data);
          alert("Error posting research: " + JSON.stringify(error.response.data));
        } else {
          alert("An unexpected error occurred.");
        }
      }
    };
  
    return (
      <FormContainer title="Post Research for Collaboration">
        <form onSubmit={postResearch}>
          <TextInput placeholder="Title" value={title} onChange={setTitle} />
          <TextInput placeholder="Research Field" value={researchField} onChange={setResearchField} />
          <TextArea placeholder="Details" value={details} onChange={setDetails} />
          <SubmitButton text="Post" />
        </form>
      </FormContainer>
    );
  };
  
  

const RequestCollaboration = () => {
    const [researchId, setResearchId] = useState("");
    const [message, setMessage] = useState("");
    const navigate = useNavigate();
  
    const requestCollab = async () => {
      if (!researchId || !message) {
        alert("Please enter all fields.");
        return;
      }
  
      try {
        await api.post(`/research/request-collaboration/${researchId}/`, { message });
        alert("Collaboration request sent successfully!");
        setResearchId("");
        setMessage("");
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          alert("Error sending request.");
        }
      }
    };
  
    return (
      <FormContainer title="Request Collaboration">
        <TextInput placeholder="Research ID" value={researchId} onChange={setResearchId} />
        <TextArea placeholder="Message" value={message} onChange={setMessage} />
        <SubmitButton text="Send Request" onClick={requestCollab} />
      </FormContainer>
    );
  };

  const CollaborationRequests = () => {
    const [requests, setRequests] = useState([]);
    const navigate = useNavigate();
  
    useEffect(() => {
      const fetchRequests = async () => {
        try {
          const response = await api.get("/research/collaboration-requests/");
          setRequests(response.data);
        } catch (error) {
          if (error.response?.status === 401) {
            alert("Unauthorized! Please log in.");
            navigate("/login");
          } else {
            alert("Error fetching collaboration requests.");
          }
        }
      };
  
      fetchRequests();
    }, []);
  
    return (
      <FormContainer title="Collaboration Requests">
        {requests.length > 0 ? (
          <ul>
            {requests.map((req) => (
              <RequestCard key={req.id} req={req} />
            ))}
          </ul>
        ) : (
          <p className="text-center text-gray-500">No pending requests</p>
        )}
      </FormContainer>
    );
  };

  const FetchUserPapers = () => {
    const [papers, setPapers] = useState([]);
    const navigate = useNavigate();
  
    const fetchUserPapers = async () => {
      try {
        const response = await api.get("/research/my_post_research_papers/"); // ✅ Fetch only user's papers
        setPapers(response.data);
      } catch (error) {
        if (error.response?.status === 401) {
          alert("Unauthorized! Please log in.");
          navigate("/login");
        } else {
          alert("Error fetching research papers.");
        }
      }
    };
  
    useEffect(() => {
      fetchUserPapers();
    }, []);
  
    return (
      <FormContainer title="My Research Papers">
        {papers.length > 0 ? (
          <ul>
            {papers.map((paper) => (
              <PaperCard key={paper.id} paper={paper} />
            ))}
          </ul>
        ) : (
          <p className="text-center text-gray-500">No research papers found.</p>
        )}
      </FormContainer>
    );
  };
 

  // ✅ Collaboration Request Card Component
  const RequestCard = ({ req }) => (
    <li className="p-4 border rounded mb-2">
      <strong>{req.requester_username}</strong> sent you a collaboration request <br />
      
      <strong>Message:</strong> {req.message}
    </li>
  );
  

// ✅ Reusable Components
const FormContainer = ({ title, children }) => (
  <div className="bg-white shadow-md rounded-lg p-6 mb-6">
    <h2 className="text-xl font-semibold mb-4">{title}</h2>
    {children}
  </div>
);

const TextInput = ({ placeholder, value, onChange }) => (
  <input type="text" placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} required className="w-full border p-2 mb-4" />
);

const TextArea = ({ placeholder, value, onChange }) => (
  <textarea placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} required className="w-full border p-2 mb-4" />
);

const SubmitButton = ({ text, onClick }) => (
  <button onClick={onClick} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg w-full">
    {text}
  </button>
);

const PaperCard = ({ paper }) => (
  <li className="p-4 border rounded mb-2">
    {paper.title} - {paper.details}{paper.author} -{" "}
    {/* <a href={`/research/${paper.download_url}`} download className="text-blue-600">
      Download
    </a> */}
    
  </li>
);

export default Research;
