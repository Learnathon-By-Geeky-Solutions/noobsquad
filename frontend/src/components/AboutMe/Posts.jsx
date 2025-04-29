import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import PropTypes from "prop-types";
import api from "../../api/axios"; // your API wrapper
import Post from "../Post";

const Posts = ({ token }) => {
  const { username } = useParams();
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserAndPosts = async () => {
      try {
        let userId = null;
        const profile = await api.get(`/user/username/${username}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        userId = profile.data;
        console.log("Fetched user ID:", userId);


        const url = userId ? `/posts/?user_id=${userId}` : "/posts";
        console.log("url:", url)
        const response = await api.get(url);
        setPosts(response.data.posts);
      } catch (err) {
        console.error("Error fetching posts:", err);
        setError("Failed to load posts.");
      } finally {
        setLoading(false);
      }
    };

    fetchUserAndPosts();
  }, [username, token]);

  if (loading) return <p className="text-gray-400">Loading posts...</p>;
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
  username: PropTypes.string, // Username passed as prop
  token: PropTypes.string.isRequired, // Token required for authenticated call
};

export default Posts;
