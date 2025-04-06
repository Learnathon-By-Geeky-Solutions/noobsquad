import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import axios from "axios";

const ChatPopup = ({ user, socket, onClose, refreshConversations }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);
  const currentUserId = parseInt(localStorage.getItem("user_id"));

  useEffect(() => {
    if (!user?.id) return;
  
    const token = localStorage.getItem("token");
  
    const fetchMessages = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/chat/chat/history/${user.id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setMessages(res.data);
        if (typeof refreshConversations === "function") {
          refreshConversations();
        }
      } catch (err) {
        console.error("Failed to fetch chat history", err);
      }
    };
  
    fetchMessages(); // immediate fetch on mount
  
    const interval = setInterval(fetchMessages, 1000); // auto-refresh every 5s
  
    return () => clearInterval(interval); // cleanup when component unmounts or user.id changes
  }, [user?.id]);
  
  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Receive messages
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        const isRelevant =
          (msg.sender_id === currentUserId && msg.receiver_id === user.id) ||
          (msg.sender_id === user.id && msg.receiver_id === currentUserId);

        if (isRelevant) {
          setMessages((prev) => [...prev, msg]);
        }
      } catch (err) {
        console.error("Failed to parse message", err);
        console.warn("📭 Non-JSON message from server:", event.data);
      }
    };

    socket.addEventListener("message", handleMessage);
    return () => socket.removeEventListener("message", handleMessage);
  }, [socket, user.id, currentUserId]);

  const sendMessage = () => {
    if (!input.trim()) return;

    const msg = {
      sender_id: currentUserId,
      receiver_id: user.id,
      content: input.trim(),
    };

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(msg));
      setInput("");
    } else {
      console.warn("WebSocket is not connected");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
      {/* Header */}
      <div className="bg-blue-600 text-white px-4 py-2 rounded-t-lg flex justify-between items-center ">
        <span className="font-semibold">{user.username}</span>
        <button onClick={onClose} className="text-white hover:text-gray-300 text-xl">
          ×
        </button>
      </div>

      {/* Messages */}
      <div className="h-64 p-3 overflow-y-auto text-sm space-y-1">
        {messages.map((msg, i) => (
          <div
            key={msg.id || i}
            className={`px-2 py-1 rounded-md max-w-[80%] ${
              msg.sender_id === currentUserId
                ? "bg-blue-100 ml-auto text-right"
                : "bg-gray-200 text-left"
            }`}
          >
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex border-t">
        <input
          className="flex-1 p-2 text-sm outline-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
        />
        <button
          onClick={sendMessage}
          className="bg-blue-500 text-white px-4 text-sm font-semibold"
        >
          Send
        </button>
      </div>
    </div>
  );
};

// ✅ Prop Validation
ChatPopup.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.number.isRequired,
    username: PropTypes.string.isRequired,
    avatar: PropTypes.string,
  }).isRequired,
  socket: PropTypes.instanceOf(WebSocket),
  onClose: PropTypes.func.isRequired,
  refreshConversations: PropTypes.func,
};

export default ChatPopup;
