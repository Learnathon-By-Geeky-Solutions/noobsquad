import { useLocation } from "react-router-dom";
import PostCard from "./PostCard";

const SearchResults = () => {
  const { state } = useLocation();
  const { posts = [], keyword = "" } = state || {};
  
  return (
    <div className="mt-20 flex flex-col w-1/2 space-y-8 mx-auto min-h-screen">
      {keyword && <p className="text-gray-500">Showing results for "{keyword}"</p>}
      <PostCard posts={posts} />
      {keyword && posts.length === 0 && <p>No posts found for "{keyword}"</p>}
    </div>
  );
};

export default SearchResults;