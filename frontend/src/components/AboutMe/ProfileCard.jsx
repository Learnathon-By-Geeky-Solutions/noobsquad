import { useEffect, useState } from "react";
import axios from "axios";
import {
  Mail, University, User, Building2, CheckCircle2, CircleX, Briefcase, Users, MessageSquare, GraduationCap
} from "lucide-react";

const ProfileCard = () => {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("No token found. Please log in.");
      return;
    }

    axios
      .get("http://localhost:8000/auth/users/me/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => setUser(response.data))
      .catch((err) => {
        if (err.response) {
          setError(err.response.data.detail || "An error occurred");
        } else {
          setError("Failed to connect to server");
        }
      });
  }, []);

  if (error) return <p className="text-center text-red-500 mt-10">{error}</p>;

  if (!user) return <p className="text-center text-gray-500 mt-10">Loading...</p>;

  return (
    <div className="bg-white shadow-md rounded-lg p-4">
      <div className="flex flex-col items-center">
        <img
          src={user.profile_picture ? `http://127.0.0.1:8000/uploads/profile_pictures/${user.profile_picture}` : "/default-avatar.png"}
          alt="Profile"
          className="w-24 h-24 rounded-full object-cover border-2 border-gray-300"
        />
        <h2 className="text-xl font-semibold mt-2 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-500" />
          {user.username}
        </h2>
        <p className="text-gray-600 flex items-center gap-2">
          <Mail className="w-4 h-4 text-gray-400" />
          {user.email}
        </p>
        <p className="text-sm text-gray-500 flex items-center gap-2">
          <University className="w-4 h-4 text-gray-400" />
          {user.university_name} — {user.department}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
      {user.fields_of_interest
        ? user.fields_of_interest.split(",").map((field, index) => (
            <span key={index} className="bg-blue-100 text-blue-600 text-sm px-3 py-1 rounded-full">
              {field.trim()}
            </span>
          ))
        : <p className="text-gray-500 text-sm">No fields of interest available.</p>
      }
    </div>
      </div>
    </div>
  );
};

export default ProfileCard;
