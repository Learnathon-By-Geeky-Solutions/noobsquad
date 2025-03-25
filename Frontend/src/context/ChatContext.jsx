import React, { createContext, useState } from "react";

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

  return (
    <ChatContext.Provider value={{ chatWindows, openChat, closeChat }}>
      {children}
    </ChatContext.Provider>
  );
};
