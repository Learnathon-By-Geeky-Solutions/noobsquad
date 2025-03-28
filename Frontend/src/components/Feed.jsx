import React, { useEffect, useState, useRef, useCallback } from "react";
import api from "../api/axios";
import Post from "../components/Post";


const Feed = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const observer = useRef(null); // ✅ Observer reference

  // ✅ Fetch posts from backend
  const fetchPosts = async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      console.log("🔍 Fetching posts with token:", token);

      const res = await api.get(`/posts?limit=10&offset=${offset}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log("✅ API Response:", res.data);

      if (res.data.posts.length === 0) {
        setHasMore(false); // ✅ Stop loading when no more posts exist
      } else {
        setPosts((prev) => {
          const allPosts = [...prev, ...res.data.posts];
          const uniquePosts = Array.from(new Map(allPosts.map((p) => [p.id, p])).values());
          return uniquePosts;
        });

        // ✅ Adjust offset based on returned posts
        setOffset((prev) => prev + res.data.posts.length);
      }
    } catch (err) {
      console.error("❌ Error fetching posts:", err.response?.data || err.message);
    }
    setLoading(false);
  };


  const handleUpdatePost = async (response) => {
    if (!response || !response.updated_post || !response.updated_post.id) {
      console.error("❌ Invalid updatedPost:", response);
      return;
    }
  
    const updatedPost = response.updated_post; // Extracting the actual post object
  
    setPosts((prevPosts) =>
      prevPosts.map((post) =>
        post && post.id ? (post.id === updatedPost.id ? { ...post, ...updatedPost } : post) : post
      )
    );
  
    // ✅ Re-fetch posts to get the latest data from the backend
    await fetchPosts();
  };
  


  
  

  // ✅ Function to delete a post
  const handleDeletePost = (postId) => {
    setPosts((prevPosts) => prevPosts.filter((post) => post.id !== postId));
  };

  // ✅ Intersection Observer for Lazy Loading
  const lastPostRef = useCallback((node) => {
    if (loading || !hasMore) return;

    if (observer.current) observer.current.disconnect(); // ✅ Disconnect previous observer

    observer.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) fetchPosts();
      },
      { threshold: 1 }
    );

    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  // ✅ Fetch posts on mount
  useEffect(() => {
    fetchPosts();
  }, [offset, hasMore]); // ✅ Depend on offset and hasMore

  return (
    <div className="max-w-2xl mx-auto p-4">


      {posts.map((post, index) => (
        <Post
          key={post.id}
          post={post}
          onUpdate={handleUpdatePost} // ✅ Pass update function
          onDelete={handleDeletePost} // ✅ Pass delete function
          ref={index === posts.length - 1 ? lastPostRef : null}
        />
      ))}

      {loading && <p className="text-gray-500 text-center">Loading more posts...</p>}

      {!loading && !hasMore && <p className="text-gray-500 text-center">No more posts to load.</p>}
    </div>
  );
};

export default Feed;
