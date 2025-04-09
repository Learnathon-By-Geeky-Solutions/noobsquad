import { useLocation } from "react-router-dom";
import PostCard from "./PostCard";

const SearchResults = () => {
  const { state } = useLocation();
  const { posts = [], keyword = "" } = state || {};
  
  return (
    <div className="mt-20 flex flex-col items-center space-y-4">
      {keyword && <p className="text-gray-500">Showing results for "{keyword}"</p>}
      <PostCard posts={posts} />
      {keyword && posts.length === 0 && <p>No posts found for "{keyword}"</p>}
    </div>
  );
};

export default SearchResults;