import React, { useState } from "react";
import { signup } from "../api/auth"; // Ensure correct import
import Navbar from "../components/Navbar";
import "../assets/signup.css"; // ✅ Import the CSS file

const Signup = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await signup(formData);
      alert("Signup successful!"); // ✅ Replace with better UI feedback
    } catch (error) {
      setError("Signup failed");
    }
  };

  return (
    <div className="signup-container">
      <Navbar />
      <div className="signup-box">
        <h2 className="signup-title">Join UHub Today</h2>
        <p className="signup-subtitle">Sign up to connect with your university community</p>

        {error && <p className="text-red-500 text-center">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleChange}
            required
            className="signup-input"
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
            className="signup-input"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            required
            className="signup-input"
          />
          <button type="submit" className="signup-button">
            Sign Up
          </button>
        </form>

        <p className="login-text">
          Already have an account?{" "}
          <a href="/login" className="login-link">
            Log in
          </a>
        </p>
      </div>
    </div>
  );
};

export default Signup;
