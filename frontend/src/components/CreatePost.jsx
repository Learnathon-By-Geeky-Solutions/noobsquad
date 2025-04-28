import React, { useState } from "react";
import api from "../api/axios";
import { FaImage, FaFileAlt, FaCalendarAlt } from "react-icons/fa";
import PropTypes from "prop-types";
import { useDropzone } from "react-dropzone";
import CreateEventForm from "./Events/CreateEventForm";

const CreatePost = ({ userProfile }) => {
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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null); // New state for error message
  const [eventImage, setEventImage] = useState(null);  // Added event image state

  CreatePost.propTypes = {
    userProfile: PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      email: PropTypes.string.isRequired,
      profilePicture: PropTypes.string,
    }).isRequired,
  };

  const { getRootProps: getMediaRootProps, getInputProps: getMediaInputProps } = useDropzone({
    accept: "image/*,video/*",
    onDrop: (acceptedFiles) => setMediaFile(acceptedFiles[0]),
  });

  const { getRootProps: getDocRootProps, getInputProps: getDocInputProps } = useDropzone({
    accept: ".pdf,.docx,.txt",
    onDrop: (acceptedFiles) => setDocumentFile(acceptedFiles[0]),
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUploadProgress(0);
    setErrorMessage(null); // Clear previous error

    try {
      const token = localStorage.getItem("token");
      const response = postType === "text" 
        ? await createTextPost(token) 
        : await createOtherPost(token);

      if (response?.data) {
        console.log("✅ Post created successfully:", response.data);
        resetForm();
        window.location.reload(); // Reload only on success
      }
    } catch (error) {
      handlePostError(error);
    }
  };

  const createTextPost = async (token) => {
    return await api.post(
      "/posts/create_text_post/",
      new URLSearchParams({ content }),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Authorization: `Bearer ${token}`, // Add token if required by backend
        },
      }
    );
  };

  const createOtherPost = async (token) => {
    let formData = new FormData();
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
      if (eventImage) {
        formData.append("event_image", eventImage);
      }
    }

    return await api.post(`/posts/create_${postType}_post/`, formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      },
    });
  };

  const handlePostError = (error) => {
    console.error("❌ Error creating post:", error);
    if (error.response && error.response.status === 400) {
      setErrorMessage(error.response.data.detail); // Display "Inappropriate content detected"
    } else {
      setErrorMessage("An unexpected error occurred. Please try again.");
    }
  };

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
    setUploadProgress(0);
    setErrorMessage(null); // Clear error on reset
  };

  return (
    <div className="bg-white shadow-lg p-6 rounded-xl mb-6 mt-20 md:mt-24 transition-all duration-300 hover:shadow-xl">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Create Post</h2>

      <div className="flex items-center mb-4">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Post your thoughts, notes, or nerdy rants!"
          className="border border-gray-300 p-4 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none min-h-[100px] text-gray-700"
        ></textarea>
      </div>

      <div className="flex justify-between items-center mb-4 max-w-md mx-auto">
        <button
          onClick={() => setPostType("media")}
          className={`p-3 rounded-lg flex items-center gap-2 transition-all duration-200 ${
            postType === "media" 
              ? "bg-blue-500 text-white shadow-md transform scale-105" 
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <FaImage size={20} />
          <span>Media</span>
        </button>
        <button
          onClick={() => setPostType("document")}
          className={`p-3 rounded-lg flex items-center gap-2 transition-all duration-200 ${
            postType === "document" 
              ? "bg-blue-500 text-white shadow-md transform scale-105" 
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <FaFileAlt size={20} />
          <span>Document</span>
        </button>
        <button
          onClick={() => setPostType("event")}
          className={`p-3 rounded-lg flex items-center gap-2 transition-all duration-200 ${
            postType === "event" 
              ? "bg-blue-500 text-white shadow-md transform scale-105" 
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <FaCalendarAlt size={20} />
          <span>Event</span>
        </button>
      </div>

      {postType === "media" && (
        <div {...getMediaRootProps()} className="border-2 border-dashed border-gray-300 p-8 text-center rounded-lg mb-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-all duration-200">
          <input {...getMediaInputProps()} />
          {mediaFile ? (
            <p className="text-green-600 font-semibold text-lg">{mediaFile.name}</p>
          ) : (
            <div className="space-y-2">
              <FaImage className="mx-auto text-gray-400" size={32} />
              <p className="text-gray-500">Drag & Drop or Click to Upload Media</p>
            </div>
          )}
        </div>
      )}

      {postType === "document" && (
        <div {...getDocRootProps()} className="border-2 border-dashed border-gray-300 p-8 text-center rounded-lg mb-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-all duration-200">
          <input {...getDocInputProps()} />
          {documentFile ? (
            <p className="text-green-600 font-semibold text-lg">{documentFile.name}</p>
          ) : (
            <div className="space-y-2">
              <FaFileAlt className="mx-auto text-gray-400" size={32} />
              <p className="text-gray-500">Drag & Drop or Click to Upload Document</p>
            </div>
          )}
        </div>
      )}

      {postType === "event" && (
        <div className="space-y-4 bg-gray-50 p-6 rounded-lg">
          <div className="mb-4">
            <label htmlFor="eventTitle" className="block text-sm font-semibold text-gray-700 mb-2">
              Event Title
            </label>
            <input
              type="text"
              id="eventTitle"
              className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={eventTitle}
              onChange={(e) => setEventTitle(e.target.value)}
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="eventDescription" className="block text-sm font-semibold text-gray-700 mb-2">
              Event Description
            </label>
            <textarea
              id="eventDescription"
              className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 min-h-[100px]"
              value={eventDescription}
              onChange={(e) => setEventDescription(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="eventDate" className="block text-sm font-semibold text-gray-700 mb-2">
                Event Date
              </label>
              <input
                type="date"
                id="eventDate"
                className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                required
              />
            </div>

            <div>
              <label htmlFor="eventTime" className="block text-sm font-semibold text-gray-700 mb-2">
                Event Time
              </label>
              <input
                type="time"
                id="eventTime"
                className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                value={eventTime}
                onChange={(e) => setEventTime(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="mb-4">
            <label htmlFor="location" className="block text-sm font-semibold text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              id="location"
              className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div className="mb-4">
            <label htmlFor="eventImage" className="block text-sm font-semibold text-gray-700 mb-2">
              Event Image (Optional)
            </label>
            <input
              type="file"
              id="eventImage"
              className="mt-1 p-3 block w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              accept="image/*"
              onChange={(e) => setEventImage(e.target.files[0])}
            />
          </div>
        </div>
      )}

      {uploadProgress > 0 && uploadProgress < 100 && (
        <div className="w-full bg-gray-200 rounded-full h-3 mt-4 mb-2 overflow-hidden">
          <div
            className="bg-blue-600 h-full rounded-full transition-all duration-300"
            style={{ width: `${uploadProgress}%` }}
          ></div>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded">
          <p className="text-red-700">{errorMessage}</p>
        </div>
      )}

      <button 
        onClick={handleSubmit} 
        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg w-full font-semibold transition-all duration-200 transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Post
      </button>
    </div>
  );
};

export default CreatePost;