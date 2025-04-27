import React, { createContext, useState, useMemo, useContext } from "react";
import PropTypes from "prop-types";

export const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const [chatWindows, setChatWindows] = useState([]);

  const openChat = (user, refreshConversations) => {
    console.log("Opening chat with user:", user);
    
    if (!user || !user.id) {
      console.error("Invalid user object provided to openChat:", user);
      return;
    }
    
    setChatWindows((prev) => {
      const alreadyOpen = prev.find((chat) => chat.id === user.id);
      if (alreadyOpen) {
        console.log("Chat already open for user:", user.id);
        return prev;
      }
      console.log("Adding new chat window for user:", user.id);
      return [...prev, { ...user, refreshConversations }];
    });
  };

  const closeChat = (userId) => {
    setChatWindows((prev) => prev.filter((chat) => chat.id !== userId));
  };

  const resetChats = () => {
    setChatWindows([]); // ✅ close all popups (useful on logout)
  };

  const contextValue = useMemo(() => ({
    chatWindows,
    openChat,
    closeChat,
    resetChats,
  }), [chatWindows]);

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};

// ✅ Prop validation
ChatProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// ✅ Helper hook for easier consumption
export const useChat = () => useContext(ChatContext);
