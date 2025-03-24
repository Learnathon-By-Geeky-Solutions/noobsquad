import { useState } from "react";
import { login, fetchUser } from "../api/auth"; 
import { useAuth } from "../context/AuthContext";
import "../assets/login.css"; 
import Navbar from "../components/Navbar";


const Login = () => {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login: authLogin } = useAuth(); 

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };


const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError("");

  try {
    const data = await login(formData); // get access_token

    if (!data?.access_token) {
      throw new Error("Login failed: No token received");
    }

    // ✅ Store token
    localStorage.setItem("token", data.access_token);

    // ✅ Fetch user info with the token
    const user = await fetchUser();

    // ✅ Store user_id for WebSocket and user data usage
    localStorage.setItem("user_id", user.id);
    localStorage.setItem("username", user.username);

    // ✅ Use context login if needed
    await authLogin(data.access_token);

  } catch (error) {
    setError("Invalid username or password");
    console.error("Login error:", error.message);
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="login-container">
      <Navbar />
      <div className="login-box">
        <h2 className="login-title">Welcome Back</h2>
        <p className="login-subtitle">Login to access your account</p>

        {error && <p className="text-red-500 text-center">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleChange}
            required
            className="login-input"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            required
            className="login-input"
          />
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p className="signup-text">
          Don't have an account?{" "}
          <a href="/signup" className="signup-link">
            Sign up
          </a>
        </p>
      </div>
    </div>
  );
};

export default Login;
