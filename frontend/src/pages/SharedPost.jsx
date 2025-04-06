import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api/axios"; // Ensure correct API import

const SharePost = () => {
    const { shareToken } = useParams();
    const [post, setPost] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
  
    useEffect(() => {
      const fetchPost = async () => {
        try {
          const response = await api.get(`/interactions/share/${shareToken}`);
          setPost(response.data);
          console.log(response.data);
        } catch (error) {
          console.error("Error fetching post:", error);
          setError("Post not found or link is invalid.");
        }
        setLoading(false);
      };
  
      fetchPost();
    }, [shareToken]);
  
    if (loading) return <p>Loading...</p>;
    if (error) return <p className="text-red-500">{error}</p>;
  
    return (
      <div className="max-w-2xl mx-auto p-4 bg-white shadow-lg rounded-lg">
        <h2 className="text-xl font-bold">{post.title}</h2>
        <p className="mt-2 text-gray-700">{post.content}</p>
      </div>
    );
  };
  
  export default SharePost;