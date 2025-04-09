import { useState } from "react";
import api from "../../api/axios"; // Ensure correct API import path
import PostCard from "./PostCard"; // Assuming you have a PostCard component to render the posts
import { Search as SearchIcon } from "lucide-react"; // Import Lucide Search icon

const Search = () => {
  const [keyword, setKeyword] = useState("");  // Search keyword
  const [posts, setPosts] = useState([]);  // Posts matching the search
  const [error, setError] = useState("");  // Error state
  const [loading, setLoading] = useState(false);  // Loading state

  // Function to fetch search results when search button is clicked or Enter key is pressed
  const fetchSearchResults = async () => {
    if (!keyword) {
      setPosts([]);  // Clear posts if no keyword is entered
      return;
    }

    setLoading(true);  // Set loading state before starting the API request

    try {
      const response = await api.get(`/search/search?keyword=${encodeURIComponent(keyword)}`);
      setPosts(response.data.posts);  // Assuming API returns posts in `data.posts`
    } catch (error) {
      console.error("Search failed:", error);
      setError("Failed to load posts.");
    } finally {
      setLoading(false);  // Set loading to false once request is done
    }
  };

  // Function to handle Enter key press
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      fetchSearchResults();  // Trigger search on Enter key press
    }
  };

  // Return error or loading states
  if (error) return <p className="text-red-500">{error}</p>;
  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div className="md:mt-24 flex flex-col items-center space-y-4">
      {/* Search Input and Button in a row */}
      <div className="flex items-center space-x-4">
        {/* Search Input with Icon */}
        <div className="relative w-full max-w-md">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}  // Update keyword as user types
            onKeyDown={handleKeyDown}  // Trigger search when Enter is pressed
            placeholder="Search posts..."
            className="w-full p-3 pl-12 pr-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {/* Search Icon */}
          <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 w-5 h-5" />
        </div>
      </div>

      {/* Display results message */}
      {keyword && <p className="mt-2 text-gray-500">Showing results for "{keyword}"</p>}

      {/* Render the PostCard component with the fetched posts */}
      <PostCard posts={posts} />
      {keyword && posts.length === 0 && <p>No posts found for "{keyword}"</p>}
    </div>
  );
};

export default Search;
