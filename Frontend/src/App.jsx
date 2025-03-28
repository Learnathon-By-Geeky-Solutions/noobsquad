import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Newsfeed"
import CompleteProfile from "./pages/ProfileCompletion";
import { AuthProvider } from "./context/AuthContext";
import SharedPost from "./pages/SharedPost";

function App() {
  return (
    <Router>
      <AuthProvider>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/complete-profile" element={<CompleteProfile />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/posts" element={<Home />} />
            <Route path="/share/:shareToken" element={<SharedPost />} />

          </Routes>

      </AuthProvider>
    </Router>
    
  );
}

export default App;
