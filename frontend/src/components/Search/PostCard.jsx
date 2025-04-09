import { useState, useEffect } from "react";
import PropTypes from "prop-types";
import api from "../../api/axios"; // Ensure the correct API import path
import Post from "../Post"; // Assuming you have a Post component to render each post

const PostCard = ({ posts }) => {
  const [postDetails, setPostDetails] = useState({}); // State to store detailed posts
  const [error, setError] = useState(""); // For error handling

  useEffect(() => {
    const fetchPostDetails = async () => {
      try {
        // Loop through each post in the posts array
        for (const post of posts) {
          // Fetch the details of each post using the post ID
          const response = await api.get(`/posts/${post.id}`);
          setPostDetails((prevState) => ({
            ...prevState,
            [post.id]: response.data, // Store post details by post ID
          }));
        }
      } catch (error) {
        console.error("Failed to fetch post details:", error);
        setError("Failed to load post details.");
      }
    };

    // Call the fetch function when the posts prop changes
    if (posts.length > 0) {
      fetchPostDetails();
    }
  }, [posts]); // Re-run this effect when the posts array changes

  if (error) return <p className="text-red-500">{error}</p>;

  // If post details haven't been fetched yet, return a loading state
  if (Object.keys(postDetails).length < posts.length) {
    return <p className="text-gray-500">Loading post details...</p>;
  }

  return (
    <div>
      {posts.map((post) => (
        // Pass the post details to the Post component
        <Post key={post.id} post={postDetails[post.id]} />
      ))}
    </div>
  );
};

PostCard.propTypes = {
  posts: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      user_id: PropTypes.number.isRequired,
      content: PropTypes.string.isRequired,
      post_type: PropTypes.string.isRequired,
      created_at: PropTypes.string.isRequired,
      like_count: PropTypes.number.isRequired,
    })
  ).isRequired,
};

export default PostCard;
