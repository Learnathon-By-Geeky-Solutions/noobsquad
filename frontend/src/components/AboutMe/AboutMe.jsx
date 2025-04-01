import { useEffect, useState } from "react";
import axios from "axios";
import {
  Mail, University, User, Building2, CheckCircle2, CircleX, Briefcase
} from "lucide-react";

const UserProfile = () => {
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

  if (error)
    return <p className="text-center text-red-500 mt-10">{error}</p>;

  if (!user)
    return <p className="text-center text-gray-500 mt-10">Loading...</p>;

  return (
    <div className="flex justify-center mt-10 px-4">
      <div className="bg-white shadow-xl rounded-2xl p-6 w-full max-w-3xl">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
          <img
            src={
              user.profile_picture
                ? `http://127.0.0.1:8000/uploads/profile_pictures/${user.profile_picture}`
                : "/default-avatar.png"
            }
            alt="Profile"
            className="w-32 h-32 rounded-full object-cover border-2 border-gray-300"
          />
       
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <User className="w-5 h-5 text-blue-500" />
              {user.username}
            </h2>
            <p className="text-gray-600 flex items-center gap-2 mt-1">
              <Mail className="w-4 h-4 text-gray-400" />
              {user.email}
            </p>
            <p className="text-sm text-gray-500 flex items-center gap-2 mt-1">
              <University className="w-4 h-4 text-gray-400" />
              {user.university_name} — {user.department}
            </p>
          </div>
        </div>

        <div className="border-t mt-6 pt-4">
          <h3 className="text-xl font-semibold text-gray-700 mb-3">About Me</h3>
          <div className="space-y-2">
            <p className="flex items-center gap-2 text-gray-700">
              <Briefcase className="w-5 h-5 text-indigo-500" />
              <span><strong>Field of Interest:</strong> {user.fields_of_interest || "N/A"}</span>
            </p>
            <p className="flex items-center gap-2 text-gray-700">
              {user.profile_completed ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : (
                <CircleX className="w-5 h-5 text-red-500" />
              )}
              <span><strong>Profile Completed:</strong> {user.profile_completed ? "Yes" : "No"}</span>
            </p>
            <p className="flex items-center gap-2 text-gray-700">
              <Building2 className="w-5 h-5 text-blue-500" />
              <span><strong>Status:</strong> {user.is_active ? "Active" : "Inactive"}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
