import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Home,
  Search,
  UserCircle,
  LogIn,
  MessageCircle,
  Book,
  Users,
  Bell,
  UserPlus
} from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";
import { useChat } from "../context/ChatContext"; // ✅ Chat context
import NotificationBell from "./notifications/notificationbell";

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [totalUnread, setTotalUnread] = useState(0);

  const { resetChats } = useChat(); // ✅ clear all popups on logout

  const handleLogout = () => {
    logout();             // clear auth
    resetChats();         // close chat popups
    navigate("/login");   // redirect
  };

  const handleHomeClick = (e) => {
    e.preventDefault(); // Prevent default link behavior
    if (location.pathname === "/dashboard/home") {
      window.location.reload(); // ✅ Refresh only if already on posts page
    } else {
      navigate("/dashboard/home"); // ✅ Navigate if not on posts page
    }
  };

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

    const interval = setInterval(fetchUnread, 3000); // refresh every 3 seconds
    return () => clearInterval(interval);
  }, [location]);

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white shadow-md flex justify-between items-center px-6 py-4">
      {/* Logo */}
      <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2">
        <img src="/logo.png" alt="UHub Logo" className="h-10 cursor-pointer" />
      </Link>

      {/* Right-side navbar */}
      <div className="flex items-center gap-6">
        {user ? (
          <>
            <Link to="/dashboard/home" onClick={handleHomeClick} className="flex items-center gap-1 text-gray-700 hover:text-blue-600 transition">
              <Home className="w-5 h-5" />
              Home
            </Link>
            <Link to="/dashboard/suggested-users" className="flex items-center gap-1 hover:text-blue-600 transition">
              <Users className="w-5 h-5" /> Connections
            </Link> 
            <Link to="/dashboard/research" className="flex items-center gap-1 hover:text-blue-600 transition">
              <Book className="w-5 h-5" /> Research
            </Link>
            <div className="relative">
              <Link to="/dashboard/chat" className="flex items-center gap-1 hover:text-blue-600 transition">
                <MessageCircle className="w-5 h-5" /> Messages
              </Link>
              {totalUnread > 0 && (
                <span className="absolute -top-2 -right-3 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  {totalUnread}
                </span>
              )}
            </div>
            <Link to="/dashboard" className="flex items-center gap-1 text-gray-700 hover:text-blue-600 transition">
              <Search className="w-5 h-5" />
              Search
            </Link>
            <div className="relative flex items-center gap-1 text-gray-700 hover:text-blue-600 transition">
              <Bell className="w-5 h-5 cursor-pointer" />
              {user && <NotificationBell userId={user.id} />}
            </div>
            <Link to="/dashboard/AboutMe" className="flex items-center gap-1 text-gray-700 font-medium cursor-pointer">
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
    </nav>
  );
};

export default Navbar;
