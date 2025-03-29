import React, { createContext, useState, useMemo } from "react";
import PropTypes from "prop-types";

export const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const [chatWindows, setChatWindows] = useState([]);

  const openChat = (user, refreshConversations) => {
    setChatWindows((prev) => {
      const alreadyOpen = prev.find((chat) => chat.id === user.id);
      if (alreadyOpen) return prev;

      return [...prev, { ...user, refreshConversations }];
    });
  };

  const closeChat = (userId) => {
    setChatWindows((prev) => prev.filter((chat) => chat.id !== userId));
  };

  // ✅ Memoize context value to avoid re-renders in consumers
  const contextValue = useMemo(() => ({
    chatWindows,
    openChat,
    closeChat,
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
