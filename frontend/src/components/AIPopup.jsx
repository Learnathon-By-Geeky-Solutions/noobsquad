import ChatBox from "./AIChat";
import PropTypes from "prop-types";

const ChatPopupWrapper = ({ onClose, fileToSend }) => {
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
        <ChatBox initialFile={fileToSend}/>
        
      </div>
    </div>
  );
};
ChatPopupWrapper.propTypes = {
  onClose: PropTypes.func.isRequired,
  fileToSend: PropTypes.object, // file object
};

export default ChatPopupWrapper;
