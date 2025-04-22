import { useNavigate, Routes, Route } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SuggestedUsers from "../components/SuggestedUsers";
import Research from "../components/Research";
import ChatSidebar from "../components/chat/ChatSidebar";
import ChatPopup from "../components/chat/ChatPopup";
import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Home from "./Newsfeed";
import UserProfile from "../components/AboutMe/AboutMe";
import CreateEventForm from "../components/Events/CreateEventForm";
import EventPosts from "../components/Events/EventList";
import SearchResults from "../components/Search/SearchResults";
import EventDetails from "../components/Events/EventDetails";


const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedUser, setSelectedUser] = useState(null);
  const [isChatVisible, setIsChatVisible] = useState(false); // New state for chat visibility


  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate("/login");
    }
  }, [user, navigate]);

  // If user is not loaded yet, don't render the dashboard
  if (!user) return null;

  return (
    
      <div className="flex flex-col bg-gray-100" >
        <Navbar onLogoutChatClear={() => setSelectedUser(null)} onToggleChat={() => setIsChatVisible(!isChatVisible)} />

        {/* Main Dashboard Content */}
        <div className="flex flex-grow overflow-hidden">
          {/* Sidebar - Only for Chat */}
          <Routes>
            <Route path="/chat" element={<ChatSidebar onSelectUser={(user) => setSelectedUser(user)} />} />
          </Routes>
        </div>

        {/* ✅ Chat Popup shown only when logged in and user is selected */}
        {user && selectedUser && isChatVisible && (
          <ChatPopup
            user={selectedUser}
            socket={null} // Replace with actual socket if available
            onClose={() => setSelectedUser(null)}
          />
        )}

      {/* Nested Routing */}
      <Routes>
        <Route path="suggested-users" element={<SuggestedUsers />} />
        <Route path="research/*" element={<Research />} />
        <Route path="posts/*" element={<Home />} />
        <Route path="events" element={<CreateEventForm />} /> 
        <Route path="eventposts" element={<EventPosts />} />  
        <Route path="search-results" element={<SearchResults />} />
        <Route path="events/:eventId" element={<EventDetails />} />
        <Route path=":username/about" element={<UserProfile />} />
        
      </Routes>
    </div>
  );
};

export default Dashboard;
