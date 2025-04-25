import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import ProfileCard from "./ProfileCard";
import ProfileFriends from "./FriendsCard";
import Posts from "./Posts";
import ResearchProfile from "./Research";
import ProfileSuggestedFriends from "./SuggestionsCard";
import CreatePost from "../CreatePost";
import UserPapers from './UserPaper';

const UserProfile = () => {
  const { username } = useParams();
  const [user, setUser] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [currentUserId, setCurrentUserId] = useState(null); // The logged-in user
  const [activeTab, setActiveTab] = useState("posts");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("No token found. Please log in.");
      return;
    }

    const fetchUserData = async () => {
      try {
        // 1. Get current logged-in user
        const current = await axios.get("http://localhost:8000/auth/users/me/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setCurrentUserId(current.data.id);
        console.log("current.data.id:", current.data.id)

        // 2. Get visited profile user using username
        const profile = await axios.get(`http://localhost:8000/user/username/${username}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        setUser(profile.data);
        console.log("profile.id:", profile.data)
        setIsOwner(current.data.id === profile.data); // Compare for ownership
      } catch (err) {
        console.error(err);
        setError("Failed to load profile.");
      }
    };

    fetchUserData();
  }, [username]);

  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;
  if (!user) return <p className="text-center text-gray-500 mt-10">Loading...</p>;

  return (
    
      <div className="flex flex-col md:flex-row justify-left px-4 -mt-4 ">
        {/* Left Sidebar */}
        <div className="w-full md:w-1/4 space-y-4 mt-20 md:mt-24">
          <ProfileCard user={user}  isOwner={isOwner}/>
          {isOwner && <ProfileFriends userId={user.id} />}
        </div>
      
      {/* Middle Section */}
      <div className="w-full md:w-2/4 px-4 mt-20 md:mt-24 -mb-24">
        <div className="flex justify-around border-b pb-2">
          <button className={`px-4 py-2 ${activeTab === "posts" ? "font-bold" : "text-gray-600"}`} onClick={() => setActiveTab("posts")}>Posts</button>
          <button className={`px-4 py-2 ${activeTab === "research" ? "font-bold" : "text-gray-600"}`} onClick={() => setActiveTab("research")}>Research</button>
        </div>
        {activeTab === "posts" ? (
        <>
        {isOwner && (
          <div className="-mt-20 md:-mt-24">
            <CreatePost />
          </div>
        )}
        <Posts userId={user.id} isOwner={isOwner} />
      </>
      ) : (
        <div className="-mt-20 md:-mt-24">
        <ResearchProfile userId={user} isOwner={isOwner}/>
        </div>
        
      )}
      </div>
    
      
      {/* Right Sidebar (Fixed Issue) */}
      <div className="w-full md:w-1/4 space-y-4 md:sticky md:top-20 mt-20 md:mt-24">
      {isOwner && <ProfileSuggestedFriends userId={user.id} />}
      </div>
    </div>
  );
};

export default UserProfile;
