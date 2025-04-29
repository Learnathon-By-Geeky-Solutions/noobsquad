import React from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { FaGraduationCap, FaUsers, FaLightbulb, FaChalkboardTeacher } from "react-icons/fa";

const LandingPage = () => {
  const features = [
    {
      icon: <FaGraduationCap className="w-8 h-8 text-blue-500" />,
      title: "Academic Networking",
      description: "Connect with students and faculty from top universities worldwide."
    },
    {
      icon: <FaUsers className="w-8 h-8 text-blue-500" />,
      title: "Collaboration Hub",
      description: "Find research partners and join academic projects that match your interests."
    },
    {
      icon: <FaLightbulb className="w-8 h-8 text-blue-500" />,
      title: "Knowledge Sharing",
      description: "Share your research, get feedback, and learn from peers in your field."
    },
    {
      icon: <FaChalkboardTeacher className="w-8 h-8 text-blue-500" />,
      title: "Mentorship",
      description: "Connect with experienced researchers and get guidance for your academic journey."
    }
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center min-h-[600px] bg-cover bg-center text-center text-white bg-[url('/background.jpg')]">
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 to-black/80" />
        <div className="relative z-10 max-w-4xl mx-auto px-4">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Where Academic Minds <span className="text-blue-400">Connect</span>
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-gray-200">
            Join a thriving university community platform where students and faculty engage, 
            share knowledge, and build opportunities together.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup" 
              className="px-8 py-4 bg-blue-600 text-white font-bold text-lg rounded-lg hover:bg-blue-700 transition-colors transform hover:scale-105">
              Get Started
            </Link>
            <Link to="/about" 
              className="px-8 py-4 bg-white/10 backdrop-blur text-white font-bold text-lg rounded-lg hover:bg-white/20 transition-colors">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-gray-800">
            Why Choose <span className="text-blue-600">UHub</span>?
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2 text-gray-800">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">500+</div>
              <div className="text-blue-100">Universities</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">50K+</div>
              <div className="text-blue-100">Students</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">10K+</div>
              <div className="text-blue-100">Research Projects</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">5K+</div>
              <div className="text-blue-100">Collaborations</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-6 text-gray-800">
            Ready to Start Your Academic Journey?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of students and researchers who are already part of our community.
          </p>
          <Link to="/signup" 
            className="inline-block px-8 py-4 bg-blue-600 text-white font-bold text-lg rounded-lg hover:bg-blue-700 transition-colors transform hover:scale-105">
            Join UHub Today
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white font-semibold mb-4">About UHub</h3>
              <ul className="space-y-2">
                <li><Link to="/about" className="hover:text-blue-400">About Us</Link></li>
                <li><Link to="/careers" className="hover:text-blue-400">Careers</Link></li>
                <li><Link to="/press" className="hover:text-blue-400">Press</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Community</h3>
              <ul className="space-y-2">
                <li><Link to="/guidelines" className="hover:text-blue-400">Guidelines</Link></li>
                <li><Link to="/research" className="hover:text-blue-400">Research</Link></li>
                <li><Link to="/events" className="hover:text-blue-400">Events</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Legal</h3>
              <ul className="space-y-2">
                <li><Link to="/privacy" className="hover:text-blue-400">Privacy</Link></li>
                <li><Link to="/terms" className="hover:text-blue-400">Terms</Link></li>
                <li><Link to="/cookies" className="hover:text-blue-400">Cookies</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Contact</h3>
              <ul className="space-y-2">
                <li><Link to="/help" className="hover:text-blue-400">Help Center</Link></li>
                <li><Link to="/contact" className="hover:text-blue-400">Contact Us</Link></li>
                <li><Link to="/feedback" className="hover:text-blue-400">Feedback</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-center">
            <p>© 2025 UHub. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
