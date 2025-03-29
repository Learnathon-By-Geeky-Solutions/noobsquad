import React, { useState, useRef, useEffect } from "react";
import api from "../api/axios";
import { FaEdit, FaTrash, FaSave, FaTimes, FaEllipsisV, FaHeart, FaRegHeart, FaComment, FaShare } from "react-icons/fa";
import { DateTime } from "luxon";
import { useAuth } from "../context/authcontext";
import ShareBox from "./ShareBox"; // Import the ShareBox component


const Post = ({ post, onUpdate, onDelete }) => {
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [updatedContent, setUpdatedContent] = useState(content);
  const menuRef = useRef(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [updatedMedia, setUpdatedMedia] = useState(null);
  const [updatedDocument, setUpdatedDocument] = useState(null);
  const [UpdatedeventTitle, setUpdatedeventTitle] = useState(event?.title || "");
  const [UpdatedeventDescription, setUpdatedeventDescription] = useState(event?.description || "");
  const [UpdatedeventDate, setUpdatedeventDate] = useState(event?.event_date || "");
  const [UpdatedeventTime, setUpdatedeventTime] = useState(event?.event_time || "");
  const [Updatedlocation, setUpdatedlocation] = useState(event?.location || "");
  const [liked, setLiked] = useState(post.user_liked);
  const [likes, setLikes] = useState(post.total_likes);
  const [comments, setComments] = useState([]);
  const [sharing, setSharing] = useState(false);
  const [shareLink, setShareLink] = useState("");
  const [commentText, setCommentText] = useState(""); // Comment input text state
  const [replyText, setReplyText] = useState(""); // Reply input text state
  const [replyingTo, setReplyingTo] = useState(null); // Track which comment the user is replying to
  const [commenting, setCommenting] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);
  const [showShareBox, setShowShareBox] = useState(false);

  useEffect(() => {
    fetchComments();
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!post || !post.user) return null;

  const { post_type, content, created_at, user: postUser, media_url, document_url, event } = post;
  
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone; // Detect user's local timezone
  const postDateUTC = DateTime.fromISO(created_at, { zone: "utc" });  //Parse as UTC
  const postDateLocal = postDateUTC.setZone(userTimezone); // Convert to user's local timezone

  // ✅ Fix: Use `.toMillis()` instead of `.getTime()`
  const timeDiffMinutes = Math.floor((Date.now() - postDateLocal.toMillis()) / 60000);
  

  let timeAgo;
  if (timeDiffMinutes < 1) {
    timeAgo = "Just now";
  } else if (timeDiffMinutes < 60) {
    timeAgo = `${timeDiffMinutes} min ago`;
  } else if (timeDiffMinutes < 1440) {
    timeAgo = `${Math.floor(timeDiffMinutes / 60)} hours ago`;
  } else {
    timeAgo = `${Math.floor(timeDiffMinutes / 1440)} days ago`;
  }

  const isOwner = user?.id === postUser?.id;
  

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const response = await api.get(`/interactions/${post.id}/comments`);
      setComments(response.data.comments);
    } catch (error) {
      console.error("Error fetching comments:", error);
    }
    setLoadingComments(false);
  };



  const handleEdit = async () => {
    try {
      let res;
      
      if (post_type === "text") {
        // Only update text content
        res = await api.put(`/posts/update_text_post/${post.id}/`, { content: updatedContent });
      } 
      else if (post_type === "media") {
        const formData = new FormData();
        if (updatedContent) formData.append("content", updatedContent);
        if (updatedMedia) formData.append("media_file", updatedMedia);
        
        res = await api.put(`/posts/update_media_post/${post.id}/`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } 
      else if (post_type === "document") {
        const formData = new FormData();
        if (updatedContent) formData.append("content", updatedContent);
        if (updatedDocument) formData.append("document_file", updatedDocument);
  
        res = await api.put(`/posts/update_document_post/${post.id}/`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      else if (post_type === "event") {
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        const formData = new FormData();
        formData.append("event_title", UpdatedeventTitle);
        formData.append("event_description", UpdatedeventDescription);
        formData.append("event_date", UpdatedeventDate);
        formData.append("event_time", UpdatedeventTime);
        formData.append("user_timezone", userTimezone);
        formData.append("location", Updatedlocation);
        res = await api.put(`/posts/update_event_post/${post.id}/`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
  
      // Update state after successful API call
      onUpdate(res.data);
      setIsEditing(false);
    } catch (error) {
      console.error("❌ Error updating post:", error);
    }
    window.location.reload();
  };
  
  
  const handleDelete = async () => {
    try {
      await api.delete(`/posts/delete_post/${post.id}/`);
      onDelete(); // Remove post from state
    } catch (error) {
      console.error("❌ Error deleting post:", error);
    } finally {
      setShowDeleteModal(false);
      window.location.reload(); // ✅ Refresh feed
    }
  };

  const handleLike = async (postId, commentId = null) => {
    // Optimistic UI update
    setLiked((prevLiked) => !prevLiked);
    setLikes((prevLikes) => (liked ? prevLikes - 1 : prevLikes + 1));
  
    try {
      const response = await api.post(`/interactions/like`, { post_id: postId, comment_id: commentId });
  
      // Backend confirmed state (if needed for accuracy)
      setLikes(response.data.total_likes);
      setLiked(response.data.user_liked);
    } catch (error) {
      console.error("Error liking post:", error);
  
      // Revert UI in case of an error
      setLiked((prevLiked) => !prevLiked);
      setLikes((prevLikes) => (liked ? prevLikes + 1 : prevLikes - 1));
    }
  };

  const handleAddComment = async (postId, content) => {
    try {
      const response = await api.post(`/interactions/${postId}/comment`, {
        post_id: postId,
        content: content,
        parent_id: null, // No parent for root comments
      });

      if (response.status === 200){
        fetchComments();
        TimeAgo();
        setCommentText("");
      }
    } catch (error) {
      console.error("Error adding comment:", error);
    }
  };

  const handleAddReply = async (postId, parentCommentId, content) => {
    try {
      const response = await api.post(`/interactions/${postId}/comment/${parentCommentId}/reply`, {
        post_id: postId,
        content: content,
        parent_id: parentCommentId,
      });
      if (response.status === 200){
        fetchComments();
        TimeAgo();
        setReplyText(""); // Clear reply input
        setReplyingTo(null); // Close reply input
      }
      
      
    } catch (error) {
      console.error("Error adding reply:", error);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      // Make an API request to delete the comment from the backend
      const response = await fetch(`/interactions/comments/${commentId}`);
      onDelete();
      // Check if the deletion was successful
      if (!response.ok) {
        throw new Error('Failed to delete the comment');
      }
  
      // Update the state to remove the deleted comment
      setComments((prevComments) => prevComments.filter(comment => comment.id !== commentId));
      alert("Comment deleted successfully!");
    } catch (error) {
      console.error('Error deleting comment:', error);
      alert('Failed to delete the comment');
    }
  };
  

  const handleShare = async () => {
      setSharing(true);
      try {
        const response = await api.post(`/interactions/${post.id}/share/`, {
          post_id: post.id, // ✅ Send post_id in request body
        });
        setShareLink(response.data.share_link);
        setShowShareBox(true);
      } catch (error) {
        console.error("Error sharing post:", error);
      }
      setSharing(false);
  };


  const TimeAgo = (dateString) => {
    // Convert to UTC first and then to the user's local timezone
    const date = DateTime.fromISO(dateString, { zone: 'utc' });  // Parse as UTC
    const localDate = date.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone);  // Convert to local timezone
  
    const now = DateTime.local();  // Get current time in local timezone
    const seconds = Math.floor(now.diff(localDate, 'seconds').seconds); // Calculate difference in seconds
  
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  
    const timeUnits = [
      { name: 'year', seconds: 60 * 60 * 24 * 365 },
      { name: 'month', seconds: 60 * 60 * 24 * 30 },
      { name: 'day', seconds: 60 * 60 * 24 },
      { name: 'hour', seconds: 60 * 60 },
      { name: 'minute', seconds: 60 },
      { name: 'second', seconds: 1 },
    ];
  
    for (const unit of timeUnits) {
      if (Math.abs(seconds) >= unit.seconds) {
        const timeValue = Math.round(seconds / unit.seconds);
        return rtf.format(timeValue, unit.name);
      }
    }
  };




return (
  <div className="bg-white shadow-md rounded-lg p-4 mb-4 relative">
    {/* Post Header */}
    <div className="flex justify-between items-center mb-3">
      <div className="flex items-center">
        <img
          src={postUser.profile_picture}
          alt="Profile"
          className="w-10 h-10 rounded-full mr-3"
        />
        <div>
          <h3 className="font-semibold">{postUser.username}</h3>
          <p className="text-xs text-gray-500">{timeAgo}</p>
        </div>
      </div>

      {/* Post Menu */}
      <div className="relative" ref={menuRef}>
        <button
          className="text-gray-600 hover:text-gray-800 p-2"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <FaEllipsisV />
        </button>
        {menuOpen && (
          <div className="absolute right-0 mt-2 w-40 bg-white border shadow-lg rounded-lg p-2">
            {isOwner ? (
              <>
                <button
                  className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100"
                  onClick={() => setIsEditing(true)}
                >
                  ✏ Edit Post
                </button>
                <button
                  className="block w-full text-left px-4 py-2 text-red-600 hover:bg-red-100"
                  onClick={() => setShowDeleteModal(true)}
                >
                  🗑 Delete Post
                </button>
              </>
            ) : (
              <button className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100">
                🚩 Report Post
              </button>
            )}
          </div>
        )}
      </div>
    </div>

    {/* Post Content */}
    {isEditing ? (
      <div>
        <textarea
          value={updatedContent}
          onChange={(e) => setUpdatedContent(e.target.value)}
          className="border p-2 rounded w-full mb-2"
        ></textarea>

        {post.post_type === "media" && (
          <input
            type="file"
            accept="image/*,video/*"
            className="mb-2 w-full"
            onChange={(e) => setUpdatedMedia(e.target.files[0])}
          />
        )}

        {post.post_type === "document" && (
          <input
            type="file"
            accept=".pdf,.doc,.docx"
            className="mb-2 w-full"
            onChange={(e) => setUpdatedDocument(e.target.files[0])}
          />
        )}

        {post.post_type === "event" && (
          <div className="space-y-2">
            <input
              type="text"
              value={UpdatedeventTitle}
              onChange={(e) => setUpdatedeventTitle(e.target.value)}
              placeholder="Event Title *"
              className="border p-2 rounded w-full"
            />
            <textarea
              value={UpdatedeventDescription}
              onChange={(e) => setUpdatedeventDescription(e.target.value)}
              placeholder="Event Description *"
              className="border p-2 rounded w-full"
            ></textarea>
            <input
              type="date"
              value={UpdatedeventDate}
              onChange={(e) => setUpdatedeventDate(e.target.value)}
              className="border p-2 rounded w-full"
            />
            <input
              type="time"
              value={UpdatedeventTime}
              onChange={(e) => setUpdatedeventTime(e.target.value)}
              className="border p-2 rounded w-full"
            />
            <input
              type="text"
              value={Updatedlocation}
              onChange={(e) => setUpdatedlocation(e.target.value)}
              placeholder="Location"
              className="border p-2 rounded w-full"
            />
          </div>
        )}

        <div className="flex gap-2 mt-2">
          <button
            onClick={handleEdit}
            className="bg-green-500 text-white px-4 py-2 rounded flex items-center gap-1"
          >
            <FaSave /> Save
          </button>
          <button
            onClick={() => setIsEditing(false)}
            className="bg-gray-500 text-white px-4 py-2 rounded flex items-center gap-1"
          >
            <FaTimes /> Cancel
          </button>
        </div>
      </div>
    ) : (
      <div>
        <p>{post.content}</p>
        {post.post_type === "media" && post.media_url && (
          <img
            src={post.media_url}
            alt="Media"
            className="w-full mt-2 rounded"
          />
        )}
        {post.post_type === "document" && post.document_url && (
          <a
            href={post.document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 underline"
          >
            View Document
          </a>
        )}
        {post.post_type === "event" && event && (
          <div>
            <h3 className="font-bold text-lg">{event.title}</h3>
            <p className="text-sm text-gray-600">{event.description}</p>
            <p className="text-sm text-gray-500">📍 {event.location}</p>
            <p className="text-sm text-gray-500">
              🗓 {new Date(event.event_datetime).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    )}

    {/* Like, Comment, Share Section */}
    <div className="flex items-center justify-between mt-3 space-x-4">
      <div className="flex items-center space-x-1">
        <span className="text-gray-700">{likes} {likes === 1 ? "Like" : "Likes"}</span>
        <button
          onClick={() => handleLike(post.id)}
          className="flex items-center text-gray-700"
        >
          {liked ? <FaHeart className="text-red-500" /> : <FaRegHeart className="text-gray-500" />}
        </button>
      </div>

      <button
        onClick={() => setCommenting(true)}
        className="flex items-center text-gray-700"
      >
        <FaComment className="text-gray-500" />
        <span className="ml-1">Comment</span>
      </button>

      <button onClick={handleShare} className="flex items-center text-gray-700">
        <FaShare />
        <span className="ml-1">Share</span>
      </button>
      {showShareBox && <ShareBox shareLink={shareLink} onClose={() => setShowShareBox(false)} />}

    </div>

    {/* Comment Section */}
    {commenting && (
      <div className="mt-4">
        <input
          type="text"
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="Write a comment..."
          className="w-full p-2 mt-2 border border-gray-300 rounded-md"
        />
        <button
          onClick={() => handleAddComment(post.id, commentText)}
          className="mt-2 bg-blue-500 text-white p-2 rounded-md"
        >
          Submit Comment
        </button>
      </div>
    )}

    {/* Render Comments */}
    <div className="mt-4">
      {loadingComments ? (
        <p>Loading comments...</p> // Show loading indicator
      ) : (
        comments.map((comment) => (
          <div key={comment.id} className="ml-4 mb-2">
            {/* Parent Comment */}
            <div className="flex items-start space-x-2">
              <img
                src={comment.user.profile_picture}
                alt={comment.user.username}
                className="w-8 h-8 rounded-full"
              />
              <div className="flex justify-between w-full">
                <div>
                  <p>
                    <strong>{comment.user.username}:</strong> {comment.content}
                  </p>
                  <p className="text-sm text-gray-500">
                    {TimeAgo(comment.created_at)} {/* Function to calculate time ago */}
                  </p>
                </div>               
              </div>
            </div>

            {/* Render Replies */}
            {comment.replies && comment.replies.length > 0 && (
              <div className="ml-4 mt-2">
                {comment.replies.map((reply) => (
                  <div key={reply.id} className="flex items-start space-x-2">
                    <img
                      src={reply.user.profile_picture}
                      alt={reply.user.username}
                      className="w-8 h-8 rounded-full"
                    />
                    <div>
                      <p>
                        <strong>{reply.user.username}:</strong> {reply.content}
                      </p>
                      <p className="text-sm text-gray-500">
                        {TimeAgo(reply.created_at)} {/* Function to calculate time ago */}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button onClick={() => setReplyingTo(comment.id)} className="text-blue-500 text-sm">
              Reply
            </button>

            {/* Reply Input */}
            {replyingTo === comment.id && (
              <div className="mt-2">
                <input
                  type="text"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Write a reply..."
                  className="w-full p-2 mt-2 border border-gray-300 rounded-md"
                />
                <button
                  onClick={() => handleAddReply(post.id, comment.id, replyText)}
                  className="mt-2 bg-blue-500 text-white p-2 rounded-md"
                >
                  Submit Reply
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>


    {/* Delete Confirmation Modal */}
    {showDeleteModal && (
      <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white p-5 rounded-lg shadow-lg w-96">
          <h2 className="text-lg font-semibold mb-4">Are you sure?</h2>
          <p>Do you really want to delete this post? This action cannot be undone.</p>
          <div className="flex justify-end mt-4 space-x-2">
            <button className="bg-gray-500 text-white px-4 py-2 rounded" onClick={() => setShowDeleteModal(false)}>Cancel</button>
            <button className="bg-red-600 text-white px-4 py-2 rounded" onClick={handleDelete}>Yes, Delete</button>
          </div>
        </div>
      </div>
    )}
    

  </div>
);

}

export default Post;
