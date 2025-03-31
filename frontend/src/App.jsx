import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import CompleteProfile from "./pages/ProfileCompletion";
import { AuthProvider, useAuth } from "./context/AuthContext"; // make sure useAuth is available
import { ChatProvider } from "./context/ChatContext";
import ChatWindows from "./components/ChatWindows";
import SharedPost from "./pages/SharedPost";

function AppWrapper() {
  return (
    <Router>
      <AuthProvider>
        <ChatProvider>
          <AppRoutes />
        </ChatProvider>
      </AuthProvider>
    </Router>
  );
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/complete-profile" element={<CompleteProfile />} />
        <Route path="/dashboard/*" element={<Dashboard />} />
        <Route path="/share/:shareToken" element={<SharedPost />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>

      {/* ✅ Only show global chat popups if logged in */}
      {user && <ChatWindows />}
    </>
  );
}

export default AppWrapper;
