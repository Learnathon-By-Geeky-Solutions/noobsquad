import React from "react";
import CreatePost from "../components/CreatePost";
import Feed from "../components/Feed"; // ✅ Import Feed
import CreateEventForm from "../components/Events/CreateEventForm";
import EventList from "../components/Events/EventList";
import { useState } from "react"; 
import TopUniversityCard from "../components/University/TopUniCard";
import ProfileSuggestedFriends from "../components/AboutMe/SuggestionsCard";

const Newsfeed = () => {
  const [showCreateEventForm, setShowCreateEventForm] = useState(false);


  // Toggle visibility of Create Event Form
  const toggleCreateEventForm = () => {
    setShowCreateEventForm((prevState) => !prevState);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Main Container with Flexbox Layout */}
      <div className="flex justify-between p-6">
        {/* Left Sidebar: Create Event Form and Events Section */}
        <aside className="w-1/3 bg-white shadow-md rounded-lg p-4 overflow-y-auto mt-20"> {/* Added mt-10 for top margin */}
          {/* Dropdown or Button to Toggle Create Event Form */}
          <button
            onClick={toggleCreateEventForm}
            className="w-full py-2 px-4 bg-blue-500 text-white rounded-lg mb-4 transition-all duration-300 hover:bg-blue-600"
          >
            {showCreateEventForm ? "Hide Create Event Form" : "Create New Event"}
          </button>

          {/* Show the Create Event Form only if showCreateEventForm is true */}
          {showCreateEventForm && (
            <div className="mb-8">
              <CreateEventForm />
            </div>
          )}

          <h2 className="text-xl font-semibold mt-8 mb-4">Events</h2>
          <div className="overflow-hidden">
            <EventList />
          </div>
        </aside>

        {/* Middle Section: Post Component */}
        <main className="w-1/2  rounded-lg p-6 mt-10"> {/* Added mt-10 for top margin */}
        <div className="-mt-30 md:-mt-24"><div className="max-w-2xl mx-auto p-4">  

{/* ✅ Create Post Section */}
<CreatePost />

{/* ✅ Render Feed (fetches and displays posts) */}
<Feed />
</div></div>
          
        </main>

        {/* Right Sidebar: Currently Blank */}
        <aside className="w-1/4 mt-20 md:mt-20 rounded-lg ">
          {/* This will remain empty for now */}
          <TopUniversityCard  />
          {/* <ProfileSuggestedFriends  /> */}

        </aside>
      </div>
    </div>
  );
};


export default Newsfeed;
