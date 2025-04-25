import ResearchTabView from "../ResearchTabView";
import React, { useState } from "react";
import { Upload, FilePlus, Handshake, FlaskConical } from "lucide-react";
import UploadPaper from "../../api/UploadPaper";
import PostResearch from "../../api/PostResearch";
import CollaborationRequests from "../../api/CollaborationRequests";
import FetchUserPapers from "../../api/FetchUserPapers";
import UserPapers from "./UserPaper";

const ResearchProfile = ({ userId, isOwner }) => {
  const [requestCount, setRequestCount] = useState(0);
  console.log("User ID:", userId);

  if (!isOwner && !userId) {
    return <p>Loading...</p>;
  }

  if (!isOwner) {
    return (
      <div className="w-full min-h-fit mt-32">
        <UserPapers userId={userId} />
      </div>
    );
  }

  const ownerTabs = [
    { path: "upload", label: "Upload Paper", icon: Upload, element: <UploadPaper /> },
    { path: "post-research", label: "Post Current Work", icon: FilePlus, element: <PostResearch /> },
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
    <ResearchTabView
      
      title="Research"
      basePath="/dashboard/research"
      tabs={ownerTabs}
    />
  );
};

export default ResearchProfile;
