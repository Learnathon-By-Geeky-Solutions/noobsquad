import React, { createContext, useState } from "react";

export const ChatContext = createContext(null);

export const ChatProvider = ({ children }) => {
  const [chatWindows, setChatWindows] = useState([]);

  const openChat = (user) => {
    setChatWindows((prev) =>
      prev.find((w) => w.id === user.id) ? prev : [...prev, user]
    );
  };

  const closeChat = (userId) => {
    setChatWindows((prev) => prev.filter((w) => w.id !== userId));
  };

  return (
    <ChatContext.Provider value={{ chatWindows, openChat, closeChat }}>
      {children}
    </ChatContext.Provider>
  );
};
