import React from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar"; // ✅ imported here
import "../assets/styles.css";

const LandingPage = () => {
  return (
    <div className="h-screen flex flex-col">
      <Navbar /> {/* ✅ used here */}

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

      <footer className="footer">
        <p>© 2025 UHub. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
