import PropTypes from "prop-types";
import { Routes, Route, NavLink } from "react-router-dom";
import SearchPapers from "../api/SearchPapers";
import UploadPaper from "../api/UploadPaper";
import PostResearch from "../api/PostResearch";
import RecentPapers from "../api/RecentPapers";
import CollaborationRequests from "../api/CollaborationRequests";
import FetchUserPapers from "../api/FetchUserPapers";

import {
  Search,
  Upload,
  FilePlus,
  BookOpen,
  Handshake,
  FlaskConical,
  Loader2
} from "lucide-react";

const Research = () => {
  return (
    <div className="bg-gray-50 min-h-screen mt-20 md:mt-24">
      <div className="pt-6 pb-2 text-center">
        <h1 className="text-2xl font-bold text-gray-800">Research</h1>
      </div>

      <div className="bg-white shadow-sm rounded-xl mx-auto max-w-6xl px-4 py-4 mb-6">
        <ul className="flex flex-wrap justify-center gap-4">
          <NavTab to="/dashboard/research/search" label="Search Papers" icon={Search} />
          <NavTab to="/dashboard/research/upload" label="Upload Paper" icon={Upload} />
          <NavTab to="/dashboard/research/post-research" label="Post Current Work" icon={FilePlus} />
          <NavTab to="/dashboard/research/recent-works" label="Current Works" icon={BookOpen} />
          <NavTab to="/dashboard/research/collab-requests" label="Collab Requests" icon={Handshake} badge={3} />
          <NavTab
            to="/dashboard/research/my_post_research_papers"
            label="Currently Working"
            icon={FlaskConical}
            loading={false}
          />
        </ul>
      </div>

      <div className="max-w-6xl mx-auto p-6 bg-white shadow rounded-lg">
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

// ✅ NavTab Component
const NavTab = ({ to, label, icon: Icon, loading = false, badge = null }) => (
  <li>
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative inline-flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm transition ${
          isActive
            ? "bg-blue-600 text-white shadow"
            : "bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-600"
        }`
      }
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Icon className="w-4 h-4" />
      )}
      {label}
      {badge !== null && (
        <span className="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold">
          {badge}
        </span>
      )}
    </NavLink>
  </li>
);

// ✅ PropTypes Validation
NavTab.propTypes = {
  to: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  icon: PropTypes.elementType.isRequired,
  loading: PropTypes.bool,
  badge: PropTypes.number,
};

export default Research;
