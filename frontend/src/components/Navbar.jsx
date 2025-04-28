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
import NotificationBell from "./notifications/NotificationBell";
import ChatPopupWrapper from "./AIPopup";

import api from "../api/axios"; // Import your axios instance

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [totalUnread, setTotalUnread] = useState(0);
  const [showAiChat, setShowAiChat] = useState(false);
  const [keyword, setKeyword] = useState("");
  const { resetChats } = useChat();
  const [socket, setSocket] = useState(null);

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

  // Use WebSocket for unread counts
  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    const token = localStorage.getItem("token");
    if (!userId || !token) return;

    // Initial fetch of unread count
    const fetchInitialUnread = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/chat/chat/conversations`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const total = res.data.reduce((sum, convo) => sum + convo.unread_count, 0);
        setTotalUnread(total);
      } catch (err) {
        console.error("Error fetching initial unread count:", err);
      }
    };

    // Set up WebSocket connection
    const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || import.meta.env.VITE_API_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/chat/ws/${userId}`);

    ws.onopen = () => {
      console.log("✅ Navbar WebSocket connected");
      setSocket(ws);
      fetchInitialUnread();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'new_message':
            // Increment unread count for new messages not from current user
            if (data.sender_id !== parseInt(userId)) {
              setTotalUnread(prev => prev + 1);
            }
            break;
            
          case 'read_receipt':
            // Decrement unread count when messages are read
            setTotalUnread(prev => Math.max(0, prev - data.read_count));
            break;
            
          case 'conversation_update':
            // Update total unread count when conversation is updated
            if (data.conversation?.unread_count !== undefined) {
              setTotalUnread(prev => prev + data.conversation.unread_count);
            }
            break;
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("Navbar WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("Navbar WebSocket closed");
      setSocket(null);
    };

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
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
                className="flex items-center gap-1 hover:text-blue-600 transition relative"
              >
                <MessageCircle className="w-5 h-5" />
                <span>Messages</span>
                {totalUnread > 0 && (
                  <div className="absolute -top-2 -right-2 flex items-center justify-center">
                    <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500 text-xs text-white items-center justify-center">
                      {totalUnread}
                    </span>
                  </div>
                )}
              </Link>
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
              to={`/dashboard/${user.username}/about`}
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