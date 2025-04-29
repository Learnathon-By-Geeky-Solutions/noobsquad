import { useEffect, useRef, useState, useCallback } from "react";
import PropTypes from "prop-types";
import axios from "axios";

const ChatPopup = ({ user, socket, onClose, refreshConversations }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null); // Ref for the messages container
  const currentUserId = parseInt(localStorage.getItem("user_id"));
  const token = localStorage.getItem("token");
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const lastScrollTop = useRef(0);

  // Fetch chat history once when opening chat
  useEffect(() => {
    if (!user?.id) return;

    const fetchMessages = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/chat/chat/history/${user.id}`, {
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
  }, [user?.id, token, refreshConversations]);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    // Check if user manually scrolled up
    if (container.scrollTop < lastScrollTop.current) {
      setShouldAutoScroll(false);
    }

    // Check if scrolled to bottom
    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 50;
    
    if (isNearBottom) {
      setShouldAutoScroll(true);
    }

    lastScrollTop.current = container.scrollTop;
  }, []);

  // Auto-scroll handling
  useEffect(() => {
    if (messages.length > 0 && shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, shouldAutoScroll]);

  // Add scroll event listener
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  const formatMessageTime = (timestamp) => {
    if (!timestamp) return '';
    
    try {
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return '';
      
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      if (isToday) {
        return date.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        });
      } else {
        return date.toLocaleDateString([], {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        });
      }
    } catch (error) {
      console.error('Error formatting timestamp:', error);
      return '';
    }
  };

  const updateMessages = useCallback((newMessage) => {
    setMessages(prev => [...prev, {
      ...newMessage,
      id: newMessage.id || Date.now(),
      timestamp: newMessage.timestamp || new Date().toISOString(),
      sender_id: newMessage.sender_id || currentUserId
    }]);
  }, [currentUserId]);

  const updateReadStatus = useCallback((data) => {
    setMessages(prev => prev.map(message => ({
      ...message,
      is_read: message.is_read || message.id <= data.last_read_id
    })));
  }, []);

  // WebSocket message handling
  useEffect(() => {
    if (!socket) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'message') {
          const isRelevant =
            (data.sender_id === currentUserId && data.receiver_id === user.id) ||
            (data.sender_id === user.id && data.receiver_id === currentUserId);

          if (isRelevant) {
            // Replace optimistic message or add new message
            setMessages(prev => {
              const optimisticMessageIndex = prev.findIndex(
                msg => msg.id === `temp-${Date.now()}` || 
                      (msg.content === data.content && 
                       msg.sender_id === data.sender_id && 
                       Math.abs(new Date(msg.timestamp) - new Date(data.timestamp)) < 1000)
              );
              
              if (optimisticMessageIndex >= 0) {
                const newMessages = [...prev];
                newMessages[optimisticMessageIndex] = data;
                return newMessages;
              }
              return [...prev, data];
            });
          }
        } else if (data.type === 'read_receipt' && data.chat_id === user.id) {
          updateReadStatus(data);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    socket.addEventListener("message", handleMessage);
    return () => socket.removeEventListener("message", handleMessage);
  }, [socket, user.id, currentUserId, updateReadStatus]);

  // Handle file selection and preview
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    if (selectedFile) {
      const isImage = selectedFile.type.startsWith("image/");
      if (isImage) {
        const previewUrl = URL.createObjectURL(selectedFile);
        setFilePreview(previewUrl);
      } else {
        setFilePreview(null);
      }
    } else {
      setFilePreview(null);
    }
  };

  // Clean up file preview URL when component unmounts or file changes
  useEffect(() => {
    return () => {
      if (filePreview) {
        URL.revokeObjectURL(filePreview);
      }
    };
  }, [filePreview]);

  // Handle file upload
  const handleFileUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${import.meta.env.VITE_API_URL}/chat/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      const { file_url } = res.data;
      const isImage = file.type.startsWith("image/");
      const fileInfo = `${file.name} • ${formatFileSize(file.size)}`;
      
      const message = {
        receiver_id: user.id,
        content: fileInfo,
        file_url,
        message_type: isImage ? "image" : "file",
        file_size: file.size,
        file_type: file.type
      };

      // Add optimistic message with local preview
      const optimisticMessage = {
        ...message,
        id: `temp-${Date.now()}`,
        sender_id: currentUserId,
        timestamp: new Date().toISOString(),
        is_read: false,
        local_preview: isImage ? filePreview : null
      };
      setMessages(prev => [...prev, optimisticMessage]);

      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
        setInput("");
        setFile(null);
        setFilePreview(null);
      } else {
        console.warn("WebSocket is not connected");
      }
    } catch (err) {
      console.error("File upload failed:", err);
      // Remove optimistic message on error
      setMessages(prev => prev.filter(msg => msg.id !== `temp-${Date.now()}`));
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

    // Add message to local state immediately with proper timestamp
    const optimisticMessage = {
      ...message,
      id: `temp-${Date.now()}`,
      sender_id: currentUserId,
      timestamp: new Date().toISOString(),
      is_read: false
    };
    setMessages(prev => [...prev, optimisticMessage]);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      setInput("");
    } else {
      console.warn("WebSocket is not connected");
      // Remove optimistic message if send failed
      setMessages(prev => prev.filter(msg => msg.id !== optimisticMessage.id));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  };

  const hasContentToSend = input.trim() || file;

  const handleImageError = useCallback((e) => {
    // Only set fallback once to prevent infinite loop
    if (!e.target.src.includes('fallback-image.png')) {
      e.target.src = "/fallback-image.png";
      console.warn("Image load failed, using fallback");
    }
  }, []);

  // Add this helper function at the top with other functions
  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Add this function to extract file info from URL
  const getFileInfo = (url, content) => {
    const filename = content || url.split('/').pop();
    // Default size if not available
    const size = '~ KB';
    const ext = filename.split('.').pop().toUpperCase();
    return { filename, size, ext };
  };

  return (
    <div className="fixed bottom-0 right-4 w-80 bg-white rounded-t-xl shadow-2xl z-50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-4 py-3 flex items-center justify-between rounded-t-xl">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <img
              src={user.avatar || "/default-avatar.png"}
              alt={user.username}
              className="w-8 h-8 rounded-full"
              onError={handleImageError}
            />
            <span className="absolute bottom-0 right-0 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></span>
          </div>
          <span className="font-semibold text-sm">{user.username}</span>
        </div>
        <div className="flex space-x-2">
          <button className="text-white hover:text-gray-200 text-lg focus:outline-none">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 12h12v-2H4v2zm0-5h12V5H4v2z" />
            </svg>
          </button>
          <button onClick={onClose} className="text-white hover:text-gray-200 text-lg focus:outline-none">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6 6l8 8m0-8l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        className="h-80 p-4 bg-gray-50 overflow-y-auto text-sm space-y-3"
      >
        {messages.map((msg, i) => (
          <div
            key={msg.id || i}
            className={`flex ${
              msg.sender_id === currentUserId ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[70%] p-2 rounded-2xl shadow-sm relative ${
                msg.sender_id === currentUserId
                  ? "bg-blue-500 text-white rounded-br-none"
                  : "bg-white text-gray-800 rounded-bl-none"
              }`}
            >
              {msg.message_type === "text" && <span>{msg.content}</span>}
              {msg.message_type === "link" && (
                <a href={msg.content} target="_blank" rel="noopener noreferrer" className="underline break-all">
                  {msg.content}
                </a>
              )}
              {msg.message_type === "image" && (
                <div className="relative group">
                  <img
                    src={msg.local_preview || msg.file_url}
                    alt={msg.content || "Shared image"}
                    className="max-w-[250px] w-full h-auto rounded-lg cursor-pointer transition-transform transform hover:scale-105"
                    onError={(e) => {
                      console.error("Image load error:", e);
                      handleImageError(e);
                    }}
                    onClick={() => window.open(msg.file_url, '_blank')}
                  />
                </div>
              )}
              {msg.message_type === "file" && !msg.file_url?.match(/\.(jpg|jpeg|png|gif|webp)$/i) && (
                <a
                  href={msg.file_url}
                  download
                  className="block no-underline hover:bg-opacity-80"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <div className="flex items-start space-x-3">
                    {/* File Type Icon */}
                    <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center bg-red-500 rounded-lg">
                      <div className="text-white text-xs font-bold">
                        {getFileInfo(msg.file_url, msg.content).ext}
                      </div>
                    </div>
                    
                    {/* File Info */}
                    <div className="flex flex-col min-w-0">
                      <span className="text-white font-medium truncate max-w-[160px]">
                        {getFileInfo(msg.file_url, msg.content).filename}
                      </span>
                      <div className="flex items-center space-x-2 text-xs text-gray-200 mt-1">
                        <span>{getFileInfo(msg.file_url, msg.content).size}</span>
                        <span>•</span>
                        <span>{msg.content.endsWith('.pdf') ? 'PDF' : 'Document'}</span>
                      </div>
                    </div>
                  </div>
                </a>
              )}
              <div
                className={`text-xs mt-1 ${
                  msg.sender_id === currentUserId ? "text-blue-200" : "text-gray-500"
                }`}
              >
                {formatMessageTime(msg.timestamp)}
                {msg.sender_id === currentUserId && (
                  <span className="ml-1">
                    {msg.is_read ? "✓✓" : "✓"}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Preview Area */}
      {hasContentToSend && (
        <div className="bg-gray-100 p-2 border-t border-b">
          {file ? (
            <>
              {filePreview ? (
                <img
                  src={filePreview}
                  alt="Preview"
                  className="max-w-[100px] h-auto rounded-lg mb-1"
                  onError={handleImageError}
                />
              ) : (
                <div className="text-sm text-gray-600">
                  File: {file.name}
                </div>
              )}
              {input.trim() && (
                <div className="text-sm text-gray-800 mt-1">{input}</div>
              )}
            </>
          ) : (
            <div className="text-sm text-gray-800">
              {input.match(/^https?:\/\/[^\s/$.?#].[^\s]*$/i) ? (
                <a href={input} target="_blank" rel="noopener noreferrer" className="underline break-all">
                  {input}
                </a>
              ) : (
                input
              )}
            </div>
          )}
        </div>
      )}

      {/* Input Area */}
      <div className="border-t bg-white p-3 flex items-center space-x-2">
        <label className="cursor-pointer text-gray-500 hover:text-blue-500" aria-label="Attach file">
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M14.5 3h-9A1.5 1.5 0 004 4.5v11A1.5 1.5 0 005.5 17h9a.5.5 0 001.5-1.5v-11A1.5 1.5 0 0014.5 3zm-9 1h9a.5.5 0 01.5.5v11a.5.5 0 01-.5.5h-9a.5.5 0 01-.5-.5v-11a.5.5 0 01.5-.5zm2 9h5a.5.5 0 000-1h-5a.5.5 0 000 1zm0-2h5a.5.5 0 000-1h-5a.5.5 0 000 1z" />
          </svg>
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.gif,.pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
            aria-label="Upload file"
          />
        </label>
        <input
          className="flex-1 p-2 text-sm bg-gray-100 rounded-full outline-none focus:ring-2 focus:ring-blue-300"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
        />
        {hasContentToSend && (
          <button
            onClick={sendMessage}
            className="bg-green-500 text-white p-2 rounded-full hover:bg-green-600 focus:outline-none"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        )}
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