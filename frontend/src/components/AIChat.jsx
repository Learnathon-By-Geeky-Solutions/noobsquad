import { useState, useRef, useEffect } from "react";

const ChatBox = () => {

  const [messages, setMessages] = useState([
      { id: Date.now(), sender: "bot", text: "Hi! How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isAnalyzingPDF, setIsAnalyzingPDF] = useState(false);
  const [file, setFile] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const storedMessages = localStorage.getItem("chatMessages");
    if (storedMessages) setMessages(JSON.parse(storedMessages));
  }, []);
  
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  const handleFileUpload = async () => {
    const token = localStorage.getItem("token");
    if (!token || !file) return;

    setIsAnalyzingPDF(true);

    // Show user message for PDF upload
    setMessages(prev => [
        ...prev,
        { id: Date.now(), sender: "user", text: `📄 Uploaded file: ${file.name}` }
    ]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/chatbot/upload_pdf/", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      setMessages(prev => [...prev, { id: Date.now(), sender: "bot", text: data.response }]);
    } catch (error) {
      console.error("Error:", error);
      setMessages(prev => [...prev, { id: Date.now(), sender: "bot", text: "❌ File upload failed." }]);
    } finally {
      setFile(null); // clear the file after upload
      setIsAnalyzingPDF(false);
    }
  };

  const handleSendMessage = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setMessages(prev => [...prev, { id: Date.now(), sender: "bot", text: "⚠️ You're not logged in." }]);
      setLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append("req", input);

      const response = await fetch("http://127.0.0.1:8000/chatbot/hugapi", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      const botMessage = { sender: "bot", text: data.response || "..." };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      setMessages(prev => [...prev, { id: Date.now(), sender: "bot", text: "❌ Error: Unable to connect." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (isAnalyzingPDF) return;

    if (file && !input.trim()) {
      setLoading(true);
      await handleFileUpload();
      setLoading(false);
    } else if (input.trim() && !file) {
      const userMessage = { id: Date.now(), sender: "user", text: input };
      setMessages(prev => [...prev, userMessage]);
      setInput("");
      setLoading(true);
      await handleSendMessage();
    } else if (file && input.trim()) {
      // Handle both file and text
      const userMessage = { sender: "user", text: input };
      setMessages(prev => [...prev, userMessage]);
      setInput("");
      setLoading(true);
      await handleFileUpload();
      await handleSendMessage();
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSend();
  };

  const handleFileChange = (e) => {
    const uploadedFile = e.target.files[0];
    setFile(uploadedFile);
  };

  return (
    <div className="max-w-96 mx-auto h-[450px] flex flex-col p-4">
      <div className="flex-1 overflow-y-auto space-y-2 mt-6 p-2 border rounded bg-gray-50">
      {messages.map((msg, idx) => (
      <div
        key={msg.id}
        className={`flex items-end gap-2 ${
          msg.sender === "user" ? "justify-end" : "justify-start"
        }`}
      >
        {msg.sender !== "user" && (
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm font-bold text-white">
            🤖
          </div>
        )}

        <div
          className={`p-3 rounded-xl max-w-[70%] text-sm break-words shadow-md ${
            msg.sender === "user"
              ? "bg-blue-500 text-white rounded-br-none"
              : "bg-gray-200 text-gray-900 rounded-bl-none"
          }`}
        >
          {msg.text.includes("📄 Uploaded file:") ? (
            <p>
              📄 Uploaded file:{" "}
              <span className="inline-block max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap align-middle">
                {msg.text.replace("📄 Uploaded file: ", "")}
              </span>
            </p>
          ) : (
            msg.text.split("\n").map((line, i) => <p key={`${msg.id}-${i}`}>{line}</p>)
          )}
        </div>

        {msg.sender === "user" && (
          <div className="w-8 h-8 bg-blue-400 text-white rounded-full flex items-center justify-center text-sm font-bold">
            🧑
          </div>
        )}
      </div>
    ))}


        {isAnalyzingPDF && (
          <div className="text-sm text-gray-500 italic">📄 AI Expert is analyzing your PDF...</div>
        )}
        {loading && !isAnalyzingPDF && (
          <div className="text-sm text-gray-500 italic">🤖 AI Expert is typing...</div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Show selected file above input */}
      {file && (
      <div className="flex items-center justify-between text-sm text-gray-600 mb-2 p-2 bg-gray-100 border rounded">
        <div className="truncate max-w-[85%]">
          Selected file:{" "}
          <strong className="inline-block max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap align-middle">
            {file.name}
          </strong>
        </div>
        <button
          onClick={() => setFile(null)}
          className="ml-2 text-red-500 hover:text-red-700 font-bold"
          title="Remove file"
        >
          ×
        </button>
      </div>
    )}

    <div className="flex items-end gap-2 mt-2">
      <div className="flex-1 relative">
        <textarea
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
          }}
          onKeyDown={handleKeyPress}
          placeholder="Type your message..."
          rows={1}
          className="w-full border rounded p-2 resize-none overflow-hidden max-h-40 min-h-[40px] leading-snug"
          disabled={isAnalyzingPDF}
        />
      </div>

      {/* File Upload Button */}
      <label
        htmlFor="file-upload"
        className="bg-gray-600 text-white w-8 h-8 rounded-full flex items-center justify-center cursor-pointer hover:bg-gray-400 transition"
        title="Upload PDF"
      >
        <span className="text-2xl -mt-[4px]">+</span>
      </label>
      <input
        type="file"
        id="file-upload"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Send Button */}
      <button
        onClick={handleSend}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
        disabled={loading || isAnalyzingPDF}
      >
        Send
      </button>
    </div>
    </div>
  );
};

export default ChatBox;
