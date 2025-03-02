import React from "react";
import { Link } from "react-router-dom";
import "../assets/styles.css"; // ✅ Import the styles

const LandingPage = () => {
  return (
    <div className="h-screen flex flex-col">
      {/* Navbar */}
      <nav className="navbar">
        <div className="flex items-center">
          <img src="/logo.png" alt="UHub Logo" className="h-10 mr-2" />
          <h1 className="text-xl font-bold text-gray-700">UHub</h1>
        </div>
        <div>
          <Link to="/login" className="px-4 py-2 text-blue-600 font-semibold">
            Login
          </Link>
          <Link to="/signup" className="px-4 py-2 bg-blue-600 text-white rounded-md font-semibold">
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-overlay">
          <h1 className="hero-title">Pair, Learn, and Grow with UHub</h1>
          <p className="hero-text">
            Join a thriving university community platform where students and faculty engage, share knowledge, and build opportunities together.
          </p>
          <div className="mt-6">
            <Link to="/signup" className="hero-button">Get Started</Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 UHub. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
