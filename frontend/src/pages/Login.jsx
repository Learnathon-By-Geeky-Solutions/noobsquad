import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { login } from "../api/auth";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import { GoogleLogin, googleLogout } from '@react-oauth/google';

const Login = () => {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const { login: authLogin } = useAuth();
  const location = useLocation();

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // Option 1: Use backend OAuth flow (recommended)
      window.location.href = `${import.meta.env.VITE_API_URL}/auth/google/login`;

      // Option 2: If using Google One Tap and want to POST token to backend:
      // const { credential } = credentialResponse;
      // const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/google/onetap`, { token: credential });
      // Handle login as usual with res.data.access_token
    } catch (error) {
      setError("Google login failed");
    }
  };
  useEffect(() => {
    if (location.state?.fromVerification) {
      setSuccess("Email verified! Please log in to continue.");
    }
  }, [location.state]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      localStorage.setItem("token", token);
      // Optionally fetch user and redirect
      window.location.href = "/dashboard/posts";
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const form = new URLSearchParams();
      form.append("username", formData.username);
      form.append("password", formData.password);
      const { data } = await login(form);
      if (!data?.access_token) throw new Error("Login failed");

      // Store token in localStorage
      localStorage.setItem("token", data.access_token);
      console.log("Token stored:", data.access_token);

      // Fetch user data with explicit token
      const userResponse = await axios.get(`${import.meta.env.VITE_API_URL}/auth/users/me/`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });
      console.log("User response:", userResponse);
      console.log("User data:", userResponse.data);

      // Check if the expected fields exist
      if (!userResponse.data.id || !userResponse.data.email || !userResponse.data.username) {
        throw new Error("User data is missing required fields (id, email, username)");
      }

      const userId = userResponse.data.id ?? "";
      const userEmail = userResponse.data.email ?? "";
      const userName = userResponse.data.username ?? "";
      console.log("Extracted user data:", { userId, userEmail, userName });

      // Store in localStorage with type conversion to string
      localStorage.setItem("user_id", String(userId));
      localStorage.setItem("user_email", String(userEmail));
      localStorage.setItem("username", String(userName));
      console.log("localStorage after setting:", {
        user_id: localStorage.getItem("user_id"),
        user_email: localStorage.getItem("user_email"),
        username: localStorage.getItem("username"),
      });

      await authLogin(data.access_token, formData.username);
    } catch (error) {
      console.error("Login error:", error);
      if (error.message === "Please verify your email") {
        setError(
          <>
            Please verify your email.{" "}
            <Link to="/verify-email" state={{ email: formData.username }} className="text-blue-600 hover:underline">
              Resend OTP
            </Link>
          </>
        );
      } else {
        setError(error.response?.data?.detail || "Invalid username or password");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <div className="flex justify-center items-center flex-grow">
        <div className="bg-white shadow-xl rounded-xl p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-2">Sign in</h2>

          <button
            type="button"
            className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-full py-2 mb-3 hover:bg-gray-100"
          >
            
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError("Google login failed")}
              useOneTap
            />
          </button>
 

          <div className="flex items-center mb-4">
            <hr className="flex-grow border-gray-300" />
            <span className="px-3 text-sm text-gray-500">or</span>
            <hr className="flex-grow border-gray-300" />
          </div>

          {success && <p className="text-green-500 text-sm mb-2 text-center">{success}</p>}
          {error && <p className="text-red-500 text-sm mb-2 text-center">{error}</p>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              name="username"
              placeholder="Username or Email"
              value={formData.username}
              onChange={handleChange}
              required
              aria-label="Username or email"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              aria-label="Password"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                  className="accent-blue-600"
                />
                Keep me logged in
              </label>
              <Link
                to="/forgot-password"
                state={{ email: formData.username.includes("@") ? formData.username : "" }}
                className="text-blue-600 hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white rounded-full py-2 font-semibold hover:bg-blue-700 transition"
              disabled={loading}
            >
              {loading ? "Logging in..." : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm mt-6">
            Don't have an account?{" "}
            <Link to="/signup" className="text-blue-600 hover:underline font-medium">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;