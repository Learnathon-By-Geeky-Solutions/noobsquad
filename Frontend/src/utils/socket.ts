// src/utils/socket.ts
export const connectSocket = (userId: string) => {
    return new WebSocket(`ws://localhost:8000/chat/ws/${userId}`);
  };
  