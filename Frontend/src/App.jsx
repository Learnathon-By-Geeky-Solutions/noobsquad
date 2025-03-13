import { BrowserRouter as Router, Routes, Route, Navigate  } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import CompleteProfile from "./pages/ProfileCompletion";
import { AuthProvider } from "./context/AuthContext";

function App() {
  return (
    <Router>
      <AuthProvider>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/complete-profile" element={<CompleteProfile />} />
            {/* 🔹 Use `/dashboard/*` to enable nested routing */}
            <Route path="/dashboard/*" element={<Dashboard />} />

            {/* Redirect unknown routes */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>

      </AuthProvider>
    </Router>
    
  );
}

export default App;
