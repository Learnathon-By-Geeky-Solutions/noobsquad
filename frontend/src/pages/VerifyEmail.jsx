import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { verifyOtp, resendOtp } from "../api/auth";
import Navbar from "../components/Navbar";

const VerifyEmail = () => {
  const [formData, setFormData] = useState({ email: "", otp: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state?.email) {
      setFormData((prev) => ({ ...prev, email: location.state.email }));
    }
  }, [location.state]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { data } = await verifyOtp(formData);
      localStorage.setItem("token", data.access_token);
      alert("Email verified successfully!");
      navigate("/login", { state: { email: formData.email } });
    } catch (error) {
      setError(error.response?.data?.detail || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendLoading(true);
    setResendMessage("");
    setError("");

    try {
      await resendOtp({ email: formData.email });
      setResendMessage("New OTP sent to your email");
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to resend OTP");
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <div className="flex justify-center items-center flex-grow px-4">
        <div className="bg-white shadow-xl rounded-xl p-8 w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-2">Verify Your Email</h2>
          <p className="text-center text-sm text-gray-500 mb-4">
            Enter the OTP sent to your email
          </p>

          {error && <p className="text-red-500 text-sm mb-2 text-center">{error}</p>}
          {resendMessage && (
            <p className="text-green-500 text-sm mb-2 text-center">{resendMessage}</p>
          )}

          <form onSubmit={handleVerify} className="space-y-4">
            <input
              type="email"
              name="email"
              placeholder="Institutional Email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="text"
              name="otp"
              placeholder="Enter OTP"
              value={formData.otp}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="w-full bg-blue-600 text-white rounded-full py-2 font-semibold hover:bg-blue-700 transition"
              disabled={loading}
            >
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
          </form>

          <p className="text-center text-sm mt-6">
            Didn't receive the OTP?{" "}
            <button
              onClick={handleResend}
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

export default VerifyEmail;