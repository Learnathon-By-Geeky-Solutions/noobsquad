import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import axios from "axios";

const ChatPopup = ({ user, socket, onClose, refreshConversations }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const messagesEndRef = useRef(null);
  const currentUserId = parseInt(localStorage.getItem("user_id"));
  const token = localStorage.getItem("token");

  // Fetch chat history
  useEffect(() => {
    if (!user?.id) return;

    const fetchMessages = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/chat/chat/history/${user.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setMessages(res.data);
        if (typeof refreshConversations === "function") {
          refreshConversations();
        }
      } catch (err) {
        console.error("Failed to fetch chat history", err);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 1000);
    return () => clearInterval(interval);
  }, [user?.id, refreshConversations, token]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const isRelevant =
          (msg.sender_id === currentUserId && msg.receiver_id === user.id) ||
          (msg.sender_id === user.id && msg.receiver_id === currentUserId);

        if (isRelevant) {
          setMessages((prev) => [...prev, {
            ...msg,
            id: msg.id || Date.now(), // Fallback ID for WebSocket messages
            timestamp: msg.timestamp || new Date().toISOString(),
          }]);
        }
      } catch (err) {
        console.error("Failed to parse message", err);
        console.warn("📭 Non-JSON message from server:", event.data);
      }
    };

    socket.addEventListener("message", handleMessage);
    return () => socket.removeEventListener("message", handleMessage);
  }, [socket, user.id, currentUserId]);

  // Handle file upload
  const handleFileUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/chat/upload", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      const { file_url } = res.data;
      const isImage = file_url.match(/\.(jpg|jpeg|png|gif)$/i);
      const message = {
        receiver_id: user.id,
        content: input.trim() || (isImage ? "Image" : "File"),
        file_url,
        message_type: isImage ? "image" : "file",
      };

      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
        setInput("");
        setFile(null);
      } else {
        console.warn("WebSocket is not connected");
      }
    } catch (err) {
      console.error("File upload failed:", err);
    }
  };

  // Send text or link message
  const sendMessage = () => {
    if (!input.trim() && !file) return;

    if (file) {
      handleFileUpload();
      return;
    }

    const isLink = input.match(/^https?:\/\/[^\s/$.?#].[^\s]*$/i);
    const message = {
      receiver_id: user.id,
      content: input.trim(),
      message_type: isLink ? "link" : "text",
    };

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
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
      <div className="bg-blue-600 text-white px-4 py-2 rounded-t-lg flex justify-between items-center">
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
            {msg.message_type === "text" && <span>{msg.content}</span>}
            {msg.message_type === "link" && (
              <a href={msg.content} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">
                {msg.content}
              </a>
            )}
            {msg.message_type === "image" && (
              <img
                src={`http://localhost:8000${msg.file_url}`}
                alt={msg.content || "Shared image"}
                className="max-w-full h-auto rounded"
                onError={(e) => {
                  e.target.src = "/fallback-image.png";
                  console.warn("Failed to load image:", msg.file_url);
                }}
              />
            )}
            {msg.message_type === "file" && (
              <a
                href={`http://localhost:8000${msg.file_url}`}
                download
                className="text-blue-500 underline"
              >
                {msg.content || "Download File"}
              </a>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-2">
        <input
          type="file"
          accept=".jpg,.jpeg,.png,.gif,.pdf,.docx"
          onChange={(e) => setFile(e.target.files[0])}
          className="text-sm mb-2"
        />
        <div className="flex">
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
    </div>
  );
};

// Prop Validation
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