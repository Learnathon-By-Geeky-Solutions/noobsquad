import { useEffect, useRef, useState} from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import {
  Mail, University, User, Camera
} from "lucide-react";
import { sanitizeUrl } from "../../utils/SanitizeUrl";

const ProfileCard = () => {
  const { username } = useParams();
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [showEditPopup, setShowEditPopup] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewURL, setPreviewURL] = useState(null);
  const fileInputRef = useRef();
  const [authUser, setAuthUser] = useState(null);           // Full logged-in user
  const [profileUserId, setProfileUserId] = useState(null); // Just the user ID from /user/username
  const isOwner = authUser && profileUserId && authUser.id === profileUserId;
  

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("No token found. Please log in.");
      return;
    }
  
    const fetchData = async () => {
      try {
        // 1. Get logged-in user
        const authRes = await axios.get(`${import.meta.env.VITE_API_URL}/auth/users/me/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setAuthUser(authRes.data);
        console.log("authRes.data:", authRes.data);
  
        // 2. Get profile user ID
        const profileRes = await axios.get(
          `${import.meta.env.VITE_API_URL}/user/username/${username}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        const profileId = profileRes.data;
        setProfileUserId(profileId);
        console.log("profileRes.data:", profileId);
  
        // ✅ 3. Get full profile data for that user ID
        const userRes = await axios.get(
          `${import.meta.env.VITE_API_URL}/user/profile/${profileId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setUser(userRes.data);
        console.log("user profile:", userRes.data);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load data");
      }
    };
  
    fetchData();
  }, [username]);


  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      const preview = URL.createObjectURL(file);
      setPreviewURL(preview);
      setShowEditPopup(true);
    }
  };

  const handleCancel = () => {
    setSelectedImage(null);
    setPreviewURL(null);
    setShowEditPopup(false);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", selectedImage);

    const token = localStorage.getItem("token");

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/profile/upload_picture`,
        formData,
        {
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setUser(prev => ({
        ...prev,
        profile_picture: response.data.filename,
      }));
      setShowEditPopup(false);
      setSelectedImage(null);
      setPreviewURL(null);
    } catch (err) {
      alert("Upload failed: " + (err.response?.data?.detail || "Unknown error"));
    }
  };

  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;
  if (!user) return <p className="text-center text-gray-500 mt-10">Loading...</p>;

  const currentPicture = user.profile_picture
    ? `${user.profile_picture}`
    : "/default-avatar.png";

  return (
    <div className="bg-white shadow-md rounded-lg p-4 mt-12 md:mt-12">
      <div className="flex flex-col items-center relative">
        {/* Profile Picture Container */}
        <div className="relative group w-24 h-24 rounded-full">
          <img
            src={sanitizeUrl(previewURL || currentPicture)}
            alt="Profile"
            className="w-24 h-24 rounded-full object-cover border-2 border-gray-300"
          />

        {/* Hover Overlay - only shows over the image */}
        {isOwner && (
          <button
            className="absolute inset-0 rounded-full bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition duration-300 cursor-pointer"
            onClick={triggerFileInput}
            aria-label="Change profile picture"
          >
            <Camera className="text-white w-6 h-6" />
          </button>
        )}
        

        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />
        </div>

        {/* Popup to confirm new image */}
        {isOwner && showEditPopup && previewURL && (
          <div className="absolute top-28 w-60 bg-white border border-gray-300 rounded-xl shadow-lg p-4 z-10 flex flex-col items-center">
            <img
              src={sanitizeUrl(previewURL)}
              alt="New Preview"
              className="w-20 h-20 rounded-full object-cover mb-3 border"
            />
            <p className="text-sm text-gray-700 font-medium mb-2">Use this photo?</p>
            <div className="flex gap-3">
              <button
                className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm hover:bg-blue-700 transition"
                onClick={handleUpload}
              >
                Change
              </button>
              <button
                className="bg-gray-200 text-gray-800 px-4 py-1 rounded-full text-sm hover:bg-gray-300 transition"
                onClick={handleCancel}
              >
                Back
              </button>
            </div>
          </div>
        )}

        {/* User Info */}
        <h2 className="text-xl font-semibold mt-3 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-500" />
          {user.username}
        </h2>
        <p className="text-gray-600 flex items-center gap-2">
          <Mail className="w-4 h-4 text-gray-400" />
          {user.email}
        </p>
        <p className="text-sm text-gray-500 flex items-center gap-2">
          <University className="w-4 h-4 text-gray-400" />
          {user.university_name} — {user.department}
        </p>

        {/* Fields of Interest */}
        <div className="mt-2 flex flex-wrap gap-2 justify-center">
          {user.fields_of_interest
            ? user.fields_of_interest.split(",").map((field, index) => (
                <span
                  key={field.trim()}
                  className="bg-blue-100 text-blue-600 text-sm px-3 py-1 rounded-full"
                >
                  {field.trim()}
                </span>
              ))
            : (
              <p className="text-gray-500 text-sm">
                No fields of interest available.
              </p>
            )}
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;
