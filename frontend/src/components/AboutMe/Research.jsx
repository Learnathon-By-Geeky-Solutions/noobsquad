import ResearchTabView from "../ResearchTabView";
import { Upload, FilePlus, Handshake, FlaskConical } from "lucide-react";
import UploadPaper from "../../api/UploadPaper";
import PostResearch from "../../api/PostResearch";
import CollaborationRequests from "../../api/CollaborationRequests";
import FetchUserPapers from "../../api/FetchUserPapers";

const tabs = [
  { path: "upload", label: "Upload Paper", icon: Upload, element: <UploadPaper /> },
  { path: "post-research", label: "Post Current Work", icon: FilePlus, element: <PostResearch /> },
  { path: "collab-requests", label: "Collab Requests", icon: Handshake, badge: 3, element: <CollaborationRequests /> },
  { path: "my_post_research_papers", label: "Currently Working", icon: FlaskConical, element: <FetchUserPapers /> },
];

const ResearchProfile = () => (
  <ResearchTabView title="My Research" basePath="/dashboard/AboutMe" tabs={tabs} />
);

export default ResearchProfile;
