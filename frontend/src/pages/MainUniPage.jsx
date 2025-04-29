import { useEffect, useState } from "react";
import UniversitySidebar from "../components/University/MainUniversitySidebar";
import UniversityPostFeed from "../components/University/PostFeed";
import api from "../api";

export default function UniversityExplorePage() {
  const [postIds, setPostIds] = useState([]);

  useEffect(() => {
    api.get("universities/posts/by-hashtag")
      .then(res => setPostIds(res.data))
      .catch(err => console.error("Error fetching hashtag posts:", err));
    console.log("getted res", postIds)
  }, []);

  // Handle department click
  const handleDepartmentClick = (university, department) => {
    api.get(`universities/posts/university/${university}/department/${department}`)
      .then(res => {
        console.log("res:", res)
        console.log("res data:", res.data)
        setPostIds(res.data)})
      .catch(err => console.error("Error fetching department posts:", err));
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 min-h-screen bg-gray-50 mt-20 md:mt-24">
  {/* Sidebar */}
  <aside className="col-span-1">
    <UniversitySidebar onDeptClick={handleDepartmentClick} />
  </aside>

  {/* Main Feed */}
  <main className="col-span-1 md:col-span-3">
    <div className="max-w-4xl mx-auto space-y-6">
      <UniversityPostFeed postIds={postIds} />
    </div>
  </main>
</div>
  );
}
