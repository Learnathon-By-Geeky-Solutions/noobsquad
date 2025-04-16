import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Home,
  Search as SearchIcon,
  UserCircle,
  LogIn,
  MessageCircle,
  Book,
  Users,
  Bell,
  UserPlus,
  Bot
} from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";
import { useChat } from "../context/ChatContext";
import NotificationBell from "./notifications/notificationbell";
import ChatPopupWrapper from "./AIPopup";

import api from "../api/axios"; // Import your axios instance

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [totalUnread, setTotalUnread] = useState(0);
  const [showAiChat, setShowAiChat] = useState(false);
  const [keyword, setKeyword] = useState(""); // Search keyword state
  const { resetChats } = useChat();

  const handleLogout = () => {
    logout();
    resetChats();
    navigate("/login");
  };

  const handleHomeClick = (e) => {
    e.preventDefault();
    navigate("/dashboard/posts");
    window.location.reload();
  
  };

  // Fetch unread messages (unchanged)
  useEffect(() => {
    const fetchUnread = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;

      try {
        const res = await axios.get("http://localhost:8000/chat/chat/conversations", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const total = res.data.reduce((sum, convo) => sum + convo.unread_count, 0);
        setTotalUnread(total);
      } catch (err) {
        console.error("Error fetching unread messages:", err);
      }
    };

    fetchUnread();
    const interval = setInterval(fetchUnread, 3000);
    return () => clearInterval(interval);
  }, [location]);

  // Search function
  const fetchSearchResults = async () => {
    if (!keyword) return;

    try {
      const response = await api.get(`/search/search?keyword=${encodeURIComponent(keyword)}`);
      // Redirect to a search results page with the keyword and results
      navigate("/dashboard/search-results", { state: { posts: response.data.posts, keyword } });
    } catch (error) {
      console.error("Search failed:", error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      fetchSearchResults();
    }
  };

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white shadow-md flex justify-between items-center px-6 py-4">
      {/* Left Section: Logo and Search */}
      <div className="flex items-center gap-6">
        <Link to={user ? "/dashboard/posts" : "/"} className="flex items-center gap-2">
          <img src="/logo.png" alt="UHub Logo" className="h-10 cursor-pointer" />
        </Link>

        {/* Search Input */}
        {user && (
          <div className="relative w-64">
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search posts..."
              className="w-full p-2 pl-10 pr-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-5 h-5" />
          </div>
        )}
      </div>

      {/* Right Section: Navigation Links */}
      <div className="flex items-center gap-6">
        {user ? (
          <>
            <Link
              to="/dashboard/posts"
              onClick={handleHomeClick}
              className="flex items-center gap-1 text-gray-700 hover:text-blue-600 transition"
            >
              <Home className="w-5 h-5" />
              Home
            </Link>
            <Link
              to="/dashboard/suggested-users"
              className="flex items-center gap-1 hover:text-blue-600 transition"
            >
              <Users className="w-5 h-5" /> Connections
            </Link>
            <Link
              to="/dashboard/research"
              className="flex items-center gap-1 hover:text-blue-600 transition"
            >
              <Book className="w-5 h-5" /> Research
            </Link>
            <div className="relative">
              <Link
                to="/dashboard/chat"
                className="flex items-center gap-1 hover:text-blue-600 transition"
              >
                <MessageCircle className="w-5 h-5" /> Messages
              </Link>
              {totalUnread > 0 && (
                <span className="absolute -top-2 -right-3 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  {totalUnread}
                </span>
              )}
            </div>
            <button
              onClick={() => setShowAiChat((prev) => !prev)}
              className="relative flex items-center gap-1 text-gray-700 hover:text-blue-600 transition transform hover:scale-105 animate-glow"
            >
              <Bot className="w-5 h-5 animate-pulse" />
              <span className="font-semibold tracking-wide">AskU</span>
              <span className="absolute -top-1 -right-2 w-2 h-2 bg-green-500 rounded-full animate-ping"></span>
            </button>
            <div className="relative flex items-center gap-1 text-gray-700 hover:text-blue-600 transition">
              <Bell className="w-5 h-5 cursor-pointer" />
              {user && <NotificationBell userId={user.id} />}
            </div>
            <Link
              to="/dashboard/AboutMe"
              className="flex items-center gap-1 text-gray-700 font-medium cursor-pointer"
            >
              <UserCircle className="w-5 h-5" />
              Me
            </Link>
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md font-semibold"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:text-blue-700 hover:underline font-medium transition"
            >
              <LogIn className="w-5 h-5" />
              Login
            </Link>
            <Link
              to="/signup"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition font-medium"
            >
              <UserPlus className="w-5 h-5" />
              Sign Up
            </Link>
          </>
        )}
      </div>
      {showAiChat && (
  <div className="fixed bottom-20 right-6 z-50">
    <ChatPopupWrapper onClose={() => setShowAiChat(false)} />
  </div>
)}
    </nav>
  );
};

export default Navbar;