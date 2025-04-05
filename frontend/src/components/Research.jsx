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

const tabs = [
  { path: "search", label: "Search Papers", icon: Search, element: <SearchPapers /> },
  { path: "upload", label: "Upload Paper", icon: Upload, element: <UploadPaper /> },
  { path: "post-research", label: "Post Current Work", icon: FilePlus, element: <PostResearch /> },
  { path: "recent-works", label: "Current Works", icon: BookOpen, element: <RecentPapers /> },
  { path: "collab-requests", label: "Collab Requests", icon: Handshake, badge: 3, element: <CollaborationRequests /> },
  { path: "my_post_research_papers", label: "Currently Working", icon: FlaskConical, element: <FetchUserPapers /> },
];

const Research = () => (
  <ResearchTabView title="Research" basePath="/dashboard/research" tabs={tabs} />
);

export default Research;
