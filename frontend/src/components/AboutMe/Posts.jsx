import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import api from "../../api/axios"; // Ensure the correct import path
import Post from "../Post";

const Posts = ({ userId }) => {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const url = userId ? `/posts?user_id=${userId}` : "/posts"; // Adjusted endpoint
        const response = await api.get(url);
        setPosts(response.data.posts); // Ensure accessing `posts` array
      } catch (error) {
        console.error("Failed to fetch posts:", error);
        setError("Failed to load posts.");
      }
    };

    fetchPosts();
  }, [userId]);

  if (error) return <p className="text-red-500">{error}</p>;
  if (!posts.length) return <p className="text-gray-500">No posts available</p>;

  return (
    <div>
      {posts.map((post) => (
        <Post key={post.id} post={post} />
      ))}
    </div>
  );
};
Posts.propTypes = {
  userId: PropTypes.string, // Adjust the type based on your actual data type
};

export default Posts;
