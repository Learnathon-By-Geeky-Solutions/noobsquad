import React, { useState } from "react";
import ResearchTabView from "./ResearchTabView";
import {
  Search,
  Upload,
  FilePlus,
  BookOpen,
  Handshake,
  FlaskConical,
} from "lucide-react";

import SearchPapers from "../api/SearchPapers";
import UploadPaper from "../api/UploadPaper";
import PostResearch from "../api/PostResearch";
import RecentPapers from "../api/RecentPapers";
import CollaborationRequests from "../api/CollaborationRequests";
import FetchUserPapers from "../api/FetchUserPapers";

const Research = () => {
  const [requestCount, setRequestCount] = useState(0);

  const tabs = [
    { path: "search", label: "Search Papers", icon: Search, element: <SearchPapers /> },
    { path: "upload", label: "Upload Paper", icon: Upload, element: <UploadPaper /> },
    { path: "post-research", label: "Post Current Work", icon: FilePlus, element: <PostResearch /> },
    { path: "recent-works", label: "Current Works", icon: BookOpen, element: <RecentPapers /> },
    {
      path: "collab-requests",
      icon: Handshake,
      element: <CollaborationRequests setRequestCount={setRequestCount} />,
      label: (
        <div className="relative inline-flex items-center">
          <span>Collab Requests</span>
          {requestCount > 0 && (
            <span className="ml-1 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full">
              {requestCount}
            </span>
          )}
        </div>
      ),
    },
    {
      path: "my_post_research_papers",
      label: "Currently Working",
      icon: FlaskConical,
      element: <FetchUserPapers />,
    },
  ];

  return (
    <ResearchTabView title="Research" basePath="/dashboard/research" tabs={tabs} />
  );
};

export default Research;
