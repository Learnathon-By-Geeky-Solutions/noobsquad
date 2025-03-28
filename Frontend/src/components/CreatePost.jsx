import React, { useState } from "react";
import api from "../api/axios";
import { FaImage, FaFileAlt, FaCalendarAlt } from "react-icons/fa";

// ✅ Drag & Drop Library
import { useDropzone } from "react-dropzone";

const CreatePost = ({ userProfile }) => {
  // ✅ State for post details
  const [postType, setPostType] = useState("text");
  const [content, setContent] = useState("");
  const [mediaFile, setMediaFile] = useState(null);
  const [documentFile, setDocumentFile] = useState(null);
  const [eventTitle, setEventTitle] = useState("");
  const [eventDescription, setEventDescription] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [eventTime, setEventTime] = useState("");
  const [location, setLocation] = useState("");
  const [userTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone);
  const [uploadProgress, setUploadProgress] = useState(0); // ✅ Upload Progress

  // ✅ Drag & Drop for Media Files
  const { getRootProps: getMediaRootProps, getInputProps: getMediaInputProps } = useDropzone({
    accept: "image/*,video/*",
    onDrop: (acceptedFiles) => setMediaFile(acceptedFiles[0]),
  });

  // ✅ Drag & Drop for Document Files
  const { getRootProps: getDocRootProps, getInputProps: getDocInputProps } = useDropzone({
    accept: ".pdf,.docx,.txt",
    onDrop: (acceptedFiles) => setDocumentFile(acceptedFiles[0]),
  });

  // ✅ Function to submit the post
  const handleSubmit = async (e) => {
    e.preventDefault();
    let formData = new FormData();
    setUploadProgress(0); // Reset progress before upload

    try {
      let response;
      const token = localStorage.getItem("token");

      if (postType === "text") {
        response = await api.post(
          "/posts/create_text_post/",
          new URLSearchParams({ content }),
          { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
        );
      } else {
        // ✅ Add Form Data
        formData.append("content", content);
        if (postType === "media" && mediaFile) formData.append("media_file", mediaFile);
        if (postType === "document" && documentFile) formData.append("document_file", documentFile);
        if (postType === "event") {
          formData.append("event_title", eventTitle);
          formData.append("event_description", eventDescription);
          formData.append("event_date", eventDate);
          formData.append("event_time", eventTime);
          formData.append("location", location);
          formData.append("user_timezone", userTimezone);
        }

        // ✅ Axios Request with Upload Progress Tracking
        response = await api.post(`/posts/create_${postType}_post/`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          },
        });
      }

      if (response?.data) {
        console.log("✅ Post created successfully:", response.data);
        resetForm();
      }
    } catch (error) {
      console.error("❌ Error creating post:", error);
    }
    window.location.reload();
  };

  // ✅ Reset the form after successful submission
  const resetForm = () => {
    setContent("");
    setMediaFile(null);
    setDocumentFile(null);
    setEventTitle("");
    setEventDescription("");
    setEventDate("");
    setEventTime("");
    setLocation("");
    setPostType("text");
    setUploadProgress(0); // ✅ Reset progress after upload
  };

  return (
    <div className="bg-white shadow-md p-4 rounded-lg mb-4">
      <h2 className="text-lg font-semibold mb-2">Create Post</h2>

      {/* ✅ Profile Image & Input */}
      <div className="flex items-center mb-3">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="What's on your mind?"
          className="border p-2 rounded w-full"
        ></textarea>
      </div>

      {/* ✅ Post Type Selection with Icons */}
      <div className="flex justify-around mb-3">
        <button
          onClick={() => setPostType("media")}
          className={`p-2 rounded-full ${postType === "media" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
        >
          <FaImage size={20} />
        </button>
        <button
          onClick={() => setPostType("document")}
          className={`p-2 rounded-full ${postType === "document" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
        >
          <FaFileAlt size={20} />
        </button>
        <button
          onClick={() => setPostType("event")}
          className={`p-2 rounded-full ${postType === "event" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
        >
          <FaCalendarAlt size={20} />
        </button>
      </div>

      {/* ✅ Drag & Drop Media Upload */}
      {postType === "media" && (
        <div {...getMediaRootProps()} className="border-2 border-dashed p-6 text-center rounded-lg mb-3 cursor-pointer bg-gray-100">
          <input {...getMediaInputProps()} />
          {mediaFile ? (
            <p className="text-green-600 font-semibold">{mediaFile.name}</p>
          ) : (
            <p className="text-gray-500">Drag & Drop or Click to Upload Media</p>
          )}
        </div>
      )}

      {/* ✅ Drag & Drop Document Upload */}
      {postType === "document" && (
        <div {...getDocRootProps()} className="border-2 border-dashed p-6 text-center rounded-lg mb-3 cursor-pointer bg-gray-100">
          <input {...getDocInputProps()} />
          {documentFile ? (
            <p className="text-green-600 font-semibold">{documentFile.name}</p>
          ) : (
            <p className="text-gray-500">Drag & Drop or Click to Upload Document</p>
          )}
        </div>
      )}

      {/* ✅ Event Fields with Labels */}
      {postType === "event" && (
        <div className="space-y-2">
          <input type="text" value={eventTitle} onChange={(e) => setEventTitle(e.target.value)} placeholder="Event Title *" className="border p-2 rounded w-full" />
          <textarea value={eventDescription} onChange={(e) => setEventDescription(e.target.value)} placeholder="Event Description *" className="border p-2 rounded w-full"></textarea>
          <input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} className="border p-2 rounded w-full" />
          <input type="time" value={eventTime} onChange={(e) => setEventTime(e.target.value)} className="border p-2 rounded w-full" />
          <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Location" className="border p-2 rounded w-full" />
        </div>
      )}

      {/* ✅ Submit Button */}
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-4 py-2 rounded w-full">
        Post
      </button>
    </div>
  );
};

export default CreatePost;
