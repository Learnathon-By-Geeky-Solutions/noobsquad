import { useState, useEffect } from "react";
import axios from "axios";
import ProfileCard from "./ProfileCard";
import ProfileFriends from "./FriendsCard";
import Posts from "./Posts";
import ResearchProfile from "./Research";
import ProfileSuggestedFriends from "./SuggestionsCard";
import CreatePost from "../CreatePost";

const UserProfile = () => {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("posts");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("No token found. Please log in.");
      return;
    }

    axios
      .get("http://localhost:8000/auth/users/me/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => setUser(response.data))
      .catch((err) => {
        setError(err.response?.data?.detail || "Failed to connect to server");
      });
  }, []);

  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;
  if (!user) return <p className="text-center text-gray-500 mt-10">Loading...</p>;

  return (
      <div className="flex flex-col md:flex-row justify-left px-4 -mt-4 ">
        {/* Left Sidebar */}
        <div className="w-full md:w-1/4 space-y-4 mt-20 md:mt-24">
          <ProfileCard user={user} />
          <ProfileFriends userId={user.id} />
        </div>
      
      {/* Middle Section */}
      <div className="w-full md:w-2/4 px-4 mt-20 md:mt-24 -mb-24">
        <div className="flex justify-around border-b pb-2">
          <button className={`px-4 py-2 ${activeTab === "posts" ? "font-bold" : "text-gray-600"}`} onClick={() => setActiveTab("posts")}>Posts</button>
          <button className={`px-4 py-2 ${activeTab === "research" ? "font-bold" : "text-gray-600"}`} onClick={() => setActiveTab("research")}>Research</button>
        </div>
        {activeTab === "posts" ? (
        <> 
          <div className="-mt-20 md:-mt-24"><CreatePost /></div>
          <Posts userId={user.id} />
        </>
      ) : (
        <div className="-mt-20 md:-mt-24">
        <ResearchProfile userId={user.id} /></div>
      )}
      </div>
    
      
      {/* Right Sidebar (Fixed Issue) */}
      <div className="w-full md:w-1/4 space-y-4 md:sticky md:top-20 mt-20 md:mt-24">
        <ProfileSuggestedFriends userId={user.id} />
      </div>
    </div>
  );
};

export default UserProfile;
