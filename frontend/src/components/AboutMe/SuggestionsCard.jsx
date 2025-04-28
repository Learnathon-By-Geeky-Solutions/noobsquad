import React, { useEffect, useState } from "react";
import axios from "axios";
import { UserPlus, Loader2 } from "lucide-react";
import UsernameLink from "./UsernameLink";

const ProfileSuggestedFriends = () => {
  const [users, setUsers] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/connections/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Only take the first 3 users
      const firstThreeUsers = response.data.slice(0, 3);

      setUsers(firstThreeUsers);
      const initialStatus = {};
      firstThreeUsers.forEach(user => {
        initialStatus[user.id] = "Connect";
      });
      setConnectionStatus(initialStatus);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const sendConnectionRequest = async (userId) => {
    if (connectionStatus[userId] === "Pending") return;
    setConnectionStatus(prev => ({ ...prev, [userId]: "Pending" }));

    try {
      const token = localStorage.getItem("token");
      await axios.post(`${import.meta.env.VITE_API_URL}/connections/connect/`, { friend_id: userId }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConnectionStatus(prev => ({ ...prev, [userId]: "Pending" }));
    } catch (error) {
      console.error("Error sending connection request:", error);
      setConnectionStatus(prev => ({ ...prev, [userId]: "Connect" }));
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white shadow-md rounded-xl p-4 relative mt-12 md:mt-12">
        {/* Top Section: "People You May Know" */}
        <div className="absolute top-0 w-full p-4">
            <h2 className="text-xl font-semibold flex items-center gap-2 text-black-500">
            People You May Know
            </h2>
        </div>

        {/* Suggested Users Section */}
        <div className="mt-12"> {/* Add margin to push content below the title */}
            <div className="flex flex-col gap-6">
            {users.length === 0 ? (
                <p className="text-gray-500 text-center">No more people to connect with 🥺</p>
            ) : (
                users.map((user) => (
                <div key={user.id} className="bg-white shadow-md rounded-xl p-5">
                    <div className="flex items-center gap-4 mb-4">
                    <img
                        src={
                        user.profile_picture
                            ? `${import.meta.env.VITE_API_URL}/uploads/profile_pictures/${user.profile_picture}`
                            : "/default-avatar.png"
                        }
                        alt="Profile"
                        className="w-14 h-14 rounded-full object-cover border-2 border-blue-500"
                    />
                    <div className="flex flex-col">
                        <h3 className="text-lg font-semibold text-gray-800"><UsernameLink username={user.username} /></h3>
                        <p className="text-sm text-gray-500">{user.university_name || "University Name"}</p>
                        <p className="text-sm text-gray-500">{user.department || "Department Name"}</p>
                    </div>
                    </div>

                    <button
                    onClick={() => sendConnectionRequest(user.id)}
                    disabled={connectionStatus[user.id] === "Pending"}
                    className={`w-full mt-4 flex justify-center items-center gap-2 text-white font-semibold py-2 px-4 rounded-md transition duration-200 ${
                        connectionStatus[user.id] === "Pending" ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
                    }`}
                    >
                    {connectionStatus[user.id] === "Pending" ? (
                        <>
                        <Loader2 className="w-4 h-4 animate-spin" /> Pending
                        </>
                    ) : (
                        <>
                        <UserPlus className="w-4 h-4" /> Pair
                        </>
                    )}
                    </button>
                </div>
                ))
            )}
            </div>

            {/* "See more" link */}
            {users.length > 3 && (
                <div className="mt-5 text-center">
                <a href={`${import.meta.env.FRONTEND_URL}/dashboard/suggested-users`} className="text-blue-500 hover:underline">
                    See more
                </a>
                </div>
            )}
            </div>

        
        </div>
  );
  
  
};
export default ProfileSuggestedFriends;
