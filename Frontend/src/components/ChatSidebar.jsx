import { useEffect, useState, useContext } from "react";
import axios from "axios";
import { ChatContext } from "../context/ChatContext";

const ChatSidebar = () => {
  const [conversations, setConversations] = useState([]);
  const { openChat } = useContext(ChatContext);

  // Fetch latest conversation list (used on mount + refresh)
  const fetchConversations = async () => {
    const token = localStorage.getItem("token");

    try {
      const res = await axios.get("http://localhost:8000/chat/chat/conversations", {
        headers: { Authorization: `Bearer ${token}` },
      });

      setConversations(res.data);
    } catch (err) {
      console.error("Error fetching conversations:", err);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  // Format ISO timestamp to short time (e.g. 4:36 PM)
  const formatTime = (isoTime) => {
    const date = new Date(isoTime);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="w-80 h-full border-r overflow-y-auto bg-white">
      <h2 className="text-xl font-bold p-4 border-b">Chats</h2>

      {conversations.length === 0 ? (
        <p className="p-4 text-gray-500">No conversations yet.</p>
      ) : (
        conversations.map((c) => {
          const normalizedUser = {
            id: c.user_id,
            username: c.username,
            avatar: c.avatar,
          };

          return (
            <div
              key={c.user_id}
              onClick={() => openChat(normalizedUser, fetchConversations)} // Pass refresh method
              className="flex items-center gap-3 p-3 hover:bg-gray-100 cursor-pointer border-b"
            >
              <img
                src={c.avatar || "/default-avatar.png"}
                alt={c.username}
                className="w-12 h-12 rounded-full object-cover"
              />
              <div className="flex-1">
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-gray-800">{c.username}</h3>
                  <span className="text-xs text-gray-400">{formatTime(c.timestamp)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-600 truncate w-full">
                    {c.is_sender ? "You: " : ""}
                    {c.last_message}
                  </p>

                  {c.unread_count > 0 && (
                    <span className="ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                      {c.unread_count}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
};

export default ChatSidebar;
