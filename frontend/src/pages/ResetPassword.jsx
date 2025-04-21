import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { forgotPassword, resetPassword } from "../api/auth";
import Navbar from "../components/Navbar";

const ResetPassword = () => {
  const [formData, setFormData] = useState({ email: "", otp: "", newPassword: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state?.email) {
      setFormData((prev) => ({ ...prev, email: location.state.email }));
    }
  }, [location.state]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    console.log(`Input changed: ${name}=${value} (type: ${typeof value})`);
    setFormData({ ...formData, [name]: value });
  };

  const handleResendOtp = async () => {
    setResendLoading(true);
    setError("");
    setSuccess("");

    try {
      await forgotPassword({ email: formData.email });
      setSuccess("New OTP sent to your email");
    } catch (error) {
      if (error.response?.status === 429) {
        setError("Too many requests. Please wait a minute and try again.");
      } else {
        setError(error.response?.data?.detail || "Failed to send OTP");
      }
    } finally {
      setResendLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    const cleanedOtp = formData.otp.trim();
    console.log(`OTP submitted: "${cleanedOtp}" (length: ${cleanedOtp.length}, type: ${typeof cleanedOtp})`);

    // Check if OTP length is exactly 6 characters
    if (cleanedOtp.length !== 6) {
      setError("Please enter a valid 6-character OTP");
      setLoading(false);
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (formData.newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    try {
      await resetPassword({
        email: formData.email,
        otp: cleanedOtp,
        new_password: formData.newPassword,
      });
      setSuccess("Password reset successfully! Redirecting to login...");
      setTimeout(() => navigate("/login"), 2000);
    } catch (error) {
      if (error.response?.status === 429) {
        setError("Too many requests. Please wait a minute and try again.");
      } else {
        setError(error.response?.data?.detail || "Password reset failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <div className="flex justify-center items-center flex-grow px-4">
        <div className="bg-white shadow-xl rounded-xl p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-2">Reset Your Password</h2>
          <p className="text-center text-sm text-gray-500 mb-4">
            Enter the OTP sent to your email and your new password
          </p>

          {error && <p className="text-red-500 text-sm mb-2 text-center">{error}</p>}
          {success && <p className="text-green-500 text-sm mb-2 text-center">{success}</p>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="email"
              name="email"
              placeholder="Institutional Email"
              value={formData.email}
              onChange={handleChange}
              required
              aria-label="Email address"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="text"
              name="otp"
              placeholder="Enter OTP"
              value={formData.otp}
              onChange={handleChange}
              required
              aria-label="OTP"
              maxLength={6}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="newPassword"
              placeholder="New Password"
              value={formData.newPassword}
              onChange={handleChange}
              required
              aria-label="New password"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="password"
              name="confirmPassword"
              placeholder="Confirm New Password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              aria-label="Confirm new password"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="w-full bg-blue-600 text-white rounded-full py-2 font-semibold hover:bg-blue-700 transition"
              disabled={loading}
            >
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          </form>

          <p className="text-center text-sm mt-6">
            Need a new OTP?{" "}
            <button
              onClick={handleResendOtp}
              className="text-blue-600 hover:underline font-medium"
              disabled={resendLoading}
            >
              {resendLoading ? "Resending..." : "Resend OTP"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
