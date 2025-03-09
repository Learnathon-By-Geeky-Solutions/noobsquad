import React, { useEffect, useState, useContext } from "react";
import { getConnections, createConnection, deleteConnection } from "../api/connections";
import { AuthContext } from "../context/AuthContext";  // Import AuthContext

const Connections = () => {
  const { user } = useContext(AuthContext);  // Get user from context
  const [connections, setConnections] = useState([]);
  const [friendId, setFriendId] = useState(""); // ✅ Correct state variable

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
  }, [user]);

  const fetchConnections = async () => {
    try {
      const data = await getConnections();
      setConnections(data);
    } catch (error) {
      console.error("Error fetching connections:", error);
    }
  };

  const handleAddConnection = async () => {
    if (!user) return alert("You must be logged in to add a connection.");
    if (!friendId) return alert("Please enter a valid user ID.");
  
    try {
      const data = await createConnection(Number(friendId)); // ✅ Convert input to number
      setConnections([...connections, data]);
      setFriendId(""); // ✅ Clear input field
    } catch (error) {
      console.error("Error adding connection:", error);
    }
  };

  const handleDeleteConnection = async (id) => {
    if (!user) return alert("You must be logged in to remove a connection.");
    try {
      await deleteConnection(id);
      setConnections(connections.filter(conn => conn.id !== id));
    } catch (error) {
      console.error("Error deleting connection:", error);
    }
  };

  if (!user) {
    return <p className="text-center text-lg text-gray-700">Please log in to manage connections.</p>;
  }

  return (
    <div className="max-w-2xl mx-auto bg-white shadow-lg rounded-lg p-6 mt-10">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 text-center">Your Connections</h2>
      <ul className="space-y-2">
        {connections.map(conn => (
          <li key={conn.id} className="flex justify-between items-center bg-gray-100 p-3 rounded-lg shadow">
            <span className="text-gray-800 font-medium">{conn.username}</span>
            <button 
              onClick={() => handleDeleteConnection(conn.id)}
              className="bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-3 rounded"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <div className="mt-6 flex space-x-2">
        <input
          type="number" // ✅ Use "number" type
          value={friendId} // ✅ Use the correct state variable
          onChange={(e) => setFriendId(e.target.value)} // ✅ Update state correctly
          placeholder="Enter friend_id"
          className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          onClick={handleAddConnection} 
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
        >
          Add Connection
        </button>
      </div>
    </div>
  );
};

export default Connections;
