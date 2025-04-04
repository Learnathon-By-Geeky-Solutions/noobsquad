import React, { useEffect, useState, useRef, useCallback } from "react";
import api from "../api/axios";
import Post from "../components/Post";
import { useLocation } from "react-router-dom";


const Feed = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const observer = useRef(null); // ✅ Observer reference
  const [highlightId, setHighlightId] = useState(null);
  const location = useLocation();



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


  // ✅ Fetch posts on mount
  useEffect(() => {
    fetchPosts();
  }, [offset, hasMore]); // ✅ Depend on offset and hasMore

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const id = queryParams.get("highlight");
    if (id) 
      setHighlightId(id);
      
  }, [location]);

  useEffect(() => {
    const fetchHighlightedPostIfNeeded = async () => {
      if (!highlightId) return;
  
      const alreadyLoaded = posts.some((p) => p.id.toString() === highlightId.toString());
      if (alreadyLoaded) return;
  
      try {
        const token = localStorage.getItem("token");
        console.log({highlightId})
        const res = await api.get(`/posts/${highlightId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
  
        if (res.data?.post) {
          setPosts((prevPosts) => {
            const exists = prevPosts.some((p) => p.id === res.data.post.id);
            if (exists) return prevPosts;
            return [res.data.post, ...prevPosts];
          });
        }
      } catch (err) {
        console.error("❌ Could not fetch highlighted post:", err.response?.data || err.message);
      }
    };
  
    fetchHighlightedPostIfNeeded();
  }, [highlightId, posts]);

  useEffect(() => {
    if (!highlightId) return;
  
    const timeout = setTimeout(() => {
      const el = document.getElementById(`post-${highlightId}`);
      console.log("🔍 Highlight element:", el);
  
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("bg-blue-200", "transition");
  
        setTimeout(() => {
          el.classList.remove("bg-blue-200");
        }, 3000);
      }
  
      setHighlightId(null); // reset after trying
    }, 100); // ⏱ small delay to wait for DOM
  
    return () => clearTimeout(timeout);
  }, [posts, highlightId]);
  
  
  



  
  const handleUpdatePost = async (response) => {
    if (!response?.updated_post?.id) {
      console.error("❌ Invalid updatedPost:", response);
      return;
    }
  
    const updatedPost = response.updated_post; // Extracting the actual post object
  
    setPosts((prevPosts) => 
      prevPosts.map((post) => {
        if (!post?.id) return post; // Return post if it's null/undefined or has no id
        return post.id === updatedPost.id ? { ...post, ...updatedPost } : post;
      })
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

  return (
    <div className="max-w-2xl mx-auto p-4">


      {posts.map((post, index) => (
        <Post
          key={post.id}
          post={post}
          onUpdate={handleUpdatePost} // ✅ Pass update function
          onDelete={handleDeletePost} // ✅ Pass delete function
          ref={index === posts.length - 1 ? lastPostRef : null}
          id={`post-${post.id}`} // Set unique ID for each post
        />
      ))}

      {loading && <p className="text-gray-500 text-center">Loading more posts...</p>}

      {!loading && !hasMore && <p className="text-gray-500 text-center">No more posts to load.</p>}
    </div>
  );
};

export default Feed;
