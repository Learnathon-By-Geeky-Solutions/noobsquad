import { Routes, Route, Link } from "react-router-dom";
import RecentPapers from "../api/RecentPapers";
import UploadPaper from "../api/UploadPaper";
import SearchPapers from "../api/SearchPapers";
import PostResearch from "../api/PostResearch";
import CollaborationRequests from "../api/CollaborationRequests";
import FetchUserPapers from "../api/FetchUserPapers";

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

export default Research;
