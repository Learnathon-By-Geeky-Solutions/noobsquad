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
    <div className="flex min-h-screen">
      <UniversitySidebar onDeptClick={handleDepartmentClick} />
      <div className="md:col-span-3">
        <UniversityPostFeed postIds={postIds} />
      </div>
    </div>
  );
}
