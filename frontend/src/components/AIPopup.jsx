import ChatBox from "./AIChat";

const ChatPopupWrapper = ({ onClose }) => {
  return (
    <div className="fixed bottom-4 right-4 z-50 w-full max-w-96">
      
      <div className="bg-white border rounded-lg shadow-lg overflow-hidden">
      <div className="p-2 border-t bg-blue-500 text-right pr-4">
          <button
            onClick={onClose}
            className="text-sm text-white hover:underline"
          >
            Close
          </button>
        </div>
        <ChatBox />
        
      </div>
    </div>
  );
};

export default ChatPopupWrapper;
