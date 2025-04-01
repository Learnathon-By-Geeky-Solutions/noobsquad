import React from "react";
import CreatePost from "../components/CreatePost";
import Feed from "../components/Feed"; // ✅ Import Feed

const Newsfeed = () => {
  return (
    <div className="max-w-2xl mx-auto p-4">  

      {/* ✅ Create Post Section */}
      <CreatePost />
      
      {/* ✅ Render Feed (fetches and displays posts) */}
      <Feed />
    </div>
  );
};

export default Newsfeed;
