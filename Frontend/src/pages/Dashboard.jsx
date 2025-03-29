import { useNavigate, Routes, Route } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SuggestedUsers from "../components/SuggestedUsers";
import Research from "../components/Research";
import ChatSidebar from "../components/ChatSidebar"; // ✅ import sidebar
import ChatPopup from "../components/ChatPopup";
import { useState } from "react";
import "../assets/Dashboard.css";
import Navbar from "../components/Navbar";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [selectedUser, setSelectedUser] = useState(null);

  if (!user) {
    navigate("/login");
    return null;
  }

  return (
    <div className="flex flex-col bg-gray-100">

      <Navbar />

      {/* Main Dashboard Content */}
      <div className="flex flex-grow overflow-hidden">
        {/* Sidebar - Only for Chat */}
        <Routes>
          <Route path="/chat" element={<ChatSidebar onSelectUser={(user) => setSelectedUser(user)} />} />
        </Routes>
      </div>

      {/* Chat Popup */}
      {selectedUser && (
        <ChatPopup
          user={selectedUser}
          socket={null} // Replace with your actual socket instance
          onClose={() => setSelectedUser(null)}
        />
      )}

      {/* Nested Routing for Suggested Users and Research */}
      <Routes>
        <Route path="suggested-users" element={<SuggestedUsers />} />
        <Route path="research/*" element={<Research />} />
      </Routes>
    </div>
  );
};

export default Dashboard;
