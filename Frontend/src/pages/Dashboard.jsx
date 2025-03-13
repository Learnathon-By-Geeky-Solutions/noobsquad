import { useNavigate, Routes, Route } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SuggestedUsers from "../components/SuggestedUsers";
import "../assets/Dashboard.css";
import Research from "../components/Research";

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

      {/* Main Dashboard Content */}
      <div className="flex flex-col items-center justify-center flex-grow">
        <h1 className="text-2xl font-bold mb-6">Welcome to Your Dashboard</h1>
        <button 
          onClick={() => navigate("/dashboard/suggested-users")} 
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300">
          👥 View Suggested Users
        </button>
        <button 
          onClick={() => navigate("/dashboard/research")} 
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300">
          📚 Research
        </button>
      </div>

      {/* Nested Routing for Suggested Users */}
      <Routes>
        <Route path="suggested-users" element={<SuggestedUsers />} />
        <Route path="research/*" element={<Research />} />
      </Routes>
    </div>
  );
};

export default Dashboard;
