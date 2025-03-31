import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import CompleteProfile from "./pages/ProfileCompletion";
import { AuthProvider } from "./context/AuthContext";
import { ChatProvider } from "./context/ChatContext";
import ChatWindows from "./components/ChatWindows"; // ✅ Import
import SharedPost from "./pages/SharedPost";

function App() {
  return (
    <Router>
      <AuthProvider>
        <ChatProvider>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/complete-profile" element={<CompleteProfile />} />
            <Route path="/dashboard/*" element={<Dashboard />} />
            <Route path="*" element={<Navigate to="/" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/share/:shareToken" element={<SharedPost />} />

          </Routes>

          {/* ✅ Render all open chat popups globally */}
          <ChatWindows />
        </ChatProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
