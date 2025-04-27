import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import Post from "../Post";

const UniversityPostFeed = ({ postIds }) => {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const token = localStorage.getItem("token");
  
        const results = await Promise.all(
          postIds.map(async (id) => {
            const res = await fetch(`${import.meta.env.VITE_API_URL}/posts/${id}`, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
              
            });
            console.log("res error:",res.json)
            if (!res.ok) {
              throw new Error(`Failed to fetch post ${id}`);
            }
  
            return res.json();
          })
        );
        console.log("result:",results)
        setPosts(results);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch posts.");
      }
    };
  
    fetchPosts();
  }, [postIds]);
  
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


  

export default UniversityPostFeed;



