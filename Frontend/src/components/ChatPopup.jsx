// src/components/ChatPopup.tsx
import { useEffect, useRef, useState } from "react";

const ChatPopup = ({ user, socket, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };
  }, []);

  const sendMessage = () => {
    const msg = { sender_id: "me", receiver_id: user.id, content: input };
    socket.send(JSON.stringify(msg));
    setMessages((prev) => [...prev, msg]);
    setInput("");
  };

  return (
    <div className="chat-popup">
      <div className="header">
        <span>{user.name}</span>
        <button onClick={onClose}>X</button>
      </div>
      <div className="messages">
        {messages.map((m, i) => <div key={i}>{m.content}</div>)}
      </div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
};
