import { useState } from "react";
import { login, fetchUser } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import { Link } from "react-router-dom";

const Login = () => {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const { login: authLogin } = useAuth();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await login(formData);
      if (!data?.access_token) throw new Error("Login failed");

      localStorage.setItem("token", data.access_token);
      const user = await fetchUser();
      localStorage.setItem("user_id", user.id);
      localStorage.setItem("username", user.username);
      await authLogin(data.access_token);
    } catch {
      setError("Invalid username or password");
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

          {/* Social Login Button */}
          <button
            type="button"
            className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-full py-2 mb-3 hover:bg-gray-100"
          >
            <img
              src="/education-svgrepo-com.svg"
              alt="University Mail Icon"
              className="w-6 h-5"
            />
            <span>Continue with University mail</span>
          </button>

          {/* Divider */}
          <div className="flex items-center mb-4">
            <hr className="flex-grow border-gray-300" />
            <span className="px-3 text-sm text-gray-500">or</span>
            <hr className="flex-grow border-gray-300" />
          </div>

          {error && <p className="text-red-500 text-sm mb-2 text-center">{error}</p>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              name="username"
              placeholder="Email or phone"
              value={formData.username}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                  className="accent-blue-600"
                /> {/* */}
                Keep me logged in
              </label>

              {/* Fixed invalid href warning */}
              <Link to="/forgot-password" className="text-blue-600 hover:underline">
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
            Don&apos;t have an account?{" "}
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
