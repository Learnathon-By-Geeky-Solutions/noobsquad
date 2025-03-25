import React, { useContext, useEffect, useState } from "react";
import { ChatContext } from "../context/ChatContext";
import ChatPopup from "./ChatPopup";

const ChatWindows = () => {
  const { chatWindows, closeChat } = useContext(ChatContext);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");

    if (userId) {
      const ws = new WebSocket(`ws://localhost:8000/chat/ws/${userId}`);

      ws.onopen = () => {
        console.log("✅ WebSocket attempting to connect...");

        // Wait 100ms and check status
        setTimeout(() => {
          if (ws.readyState === WebSocket.OPEN) {
            console.log("✅ WebSocket connection is stable");
            setSocket(ws);
          } else {
            console.warn("❌ WebSocket was closed during handshake");
          }
        }, 100);
      };

      ws.onerror = (e) => {
        console.error("❌ WebSocket error:", e);
      };

      ws.onclose = () => {
        console.warn("🔌 WebSocket closed");
      };

      return () => {
        ws.close(); // cleanup on unmount
      };
    } else {
      console.warn("⚠️ No user_id found in localStorage.");
    }
  }, []);

  if (!socket) return null; // Don't render chat popups until socket is ready

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
