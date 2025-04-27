import React, { useContext, useEffect, useState } from "react";
import { ChatContext } from "../../context/ChatContext";
import ChatPopup from "./ChatPopup";

const ChatWindows = () => {
  const { chatWindows, closeChat } = useContext(ChatContext);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");

    if (userId) {
      const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || import.meta.env.VITE_API_URL.replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/chat/ws/${userId}`);

      ws.onopen = () => {
        console.log("✅ WebSocket connection established");
        setSocket(ws);
      };

      ws.onerror = (e) => {
        console.error("❌ WebSocket error:", e);
      };

      ws.onclose = () => {
        console.warn("🔌 WebSocket closed");
        setSocket(null);
      };

      return () => {
        ws.close();
        console.log("🧹 WebSocket cleanup performed");
      };
    } else {
      console.warn("⚠️ No user_id found in localStorage.");
    }
  }, []);

  return (
    <>
      {chatWindows.map((user) => (
        <ChatPopup
          key={user.id}
          user={user}
          socket={socket}
          onClose={() => closeChat(user.id)}
          refreshConversations={user.refreshConversations}
        />
      ))}
    </>
  );
};

export default ChatWindows;