import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {fetchConnectedUsers} from "./../../api/fetchfriend";

const ProfileFriends = () => {
    const [friends, setFriends] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
  
    useEffect(() => {
      fetchConnectedUsers()
        .then(setFriends)
        .catch(() => setError("Failed to load friends."))
        .finally(() => setLoading(false));
    }, []);
  
    if (loading) return <p className="text-gray-500">Loading friends...</p>;
    if (error) return <p className="text-red-500">{error}</p>;
    if (friends.length === 0) return <p className="text-gray-500">No friends yet.</p>;
  
    return (
        <div className="max-w-md mx-auto mt-4 bg-white shadow-md rounded-xl p-4">
          <h2 className="text-xl font-bold text-blue-700 mb-3 text-center">Friends</h2>
    
          <div className="grid grid-cols-3 gap-4">
            {friends.slice(0, 6).map((friend) => (
              <div key={friend.id} className="flex flex-col items-center">
                <img
                  src={
                    friend.profile_picture
                      ? `${friend.profile_picture}`
                      : "/default-avatar.png"
                  }
                  alt="Profile"
                  className="w-14 h-14 rounded-full object-cover border-2 border-blue-500"
                />
                <p className="text-gray-800 font-medium text-sm text-center mt-2">
                  {friend.username}
                </p>
              </div>
            ))}
          </div>
    
          {friends.length > 6 && (
            <div className="text-center mt-3">
              <Link to={`${import.meta.env.FRONTEND_URL}/dashboard/suggested-users`} className="text-blue-500 hover:underline">
                See more
              </Link>
            </div>
          )}
        </div>
      );
  };
  
  export default ProfileFriends;
