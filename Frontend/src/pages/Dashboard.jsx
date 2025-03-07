import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import SuggestedUsers from "../components/SuggestedUsers";  
import "../assets/Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    navigate("/login");
    return null;
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-100">
      
      {/* Top Navbar */}
      <div className="flex justify-between items-center bg-white shadow-md px-6 py-4">
        <div className="flex items-center space-x-2 cursor-pointer">
          <img src={user.avatar || "/default-avatar.png"} alt="Profile" className="w-10 h-10 rounded-full" />
          <span className="text-lg font-medium text-gray-800">Me ▼</span>
        </div>
        <button type="button" onClick={logout} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg shadow-md transition duration-300">
          Logout
        </button>
      </div>

      {/* Suggested Users Section */}
      <div className="p-6">
        <SuggestedUsers />
      </div>
    </div>
  );
};

export default Dashboard;
