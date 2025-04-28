import { useEffect, useState, useContext } from "react";
import axios from "axios";
import { ChatContext } from "../../context/ChatContext";

const ChatSidebar = () => {
  const [conversations, setConversations] = useState([]);
  const { openChat } = useContext(ChatContext);

  // Initial fetch of conversations
  const fetchConversations = async () => {
    const token = localStorage.getItem("token");
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/chat/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setConversations(res.data);
    } catch (err) {
      console.error("Error fetching conversations:", err);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'conversation_update':
        // Update specific conversation
        setConversations(prevConversations => 
          prevConversations.map(conv => 
            conv.user_id === data.user_id ? { ...conv, ...data.conversation } : conv
          )
        );
        break;
      
      case 'new_message':
        // Update conversation list when new message arrives
        fetchConversations();
        break;

      case 'read_receipt':
        // Update unread counts
        setConversations(prevConversations =>
          prevConversations.map(conv =>
            conv.user_id === data.sender_id ? { ...conv, unread_count: 0 } : conv
          )
        );
        break;
    }
  };

  // Setup WebSocket connection
  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || import.meta.env.VITE_API_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/chat/ws/${userId}`);

    ws.onopen = () => {
      console.log("✅ ChatSidebar WebSocket connected");
      fetchConversations();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("ChatSidebar WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("ChatSidebar WebSocket closed");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  const formatTime = (isoTime) => {
    const date = new Date(isoTime);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffHours < 24) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } else if (diffHours < 48) {
      return "Yesterday";
    } else {
      return date.toLocaleDateString();
    }
  };

  const formatLastMessage = (conversation) => {
    if (conversation.message_type === "text" || conversation.message_type === "link") {
      return conversation.last_message || "";
    }
    if (conversation.message_type === "image") {
      return "📷 Image";
    }
    if (conversation.message_type === "file") {
      return "📎 File";
    }
    return "";
  };

  return (
    <aside className="w-80 h-full border-r overflow-y-auto bg-white mt-20 md:mt-24">
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

          const profileImage = c.avatar || "/default-avatar.png";

          return (
            <button
              key={c.user_id}
              type="button"
              onClick={() => openChat(normalizedUser, fetchConversations)}
              className="w-full text-left flex items-center gap-3 p-3 hover:bg-gray-100 cursor-pointer border-b focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <img
                src={profileImage}
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = "/default-avatar.png";
                }}
                alt={`${c.username}'s avatar`}
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
                    {formatLastMessage(c)}
                  </p>
                  {c.unread_count > 0 && (
                    <span className="ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                      {c.unread_count}
                    </span>
                  )}
                </div>
              </div>
            </button>
          );
        })
      )}
    </aside>
  );
};

export default ChatSidebar;