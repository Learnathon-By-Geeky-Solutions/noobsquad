import { FaCopy, FaTimes } from "react-icons/fa";

const ShareBox = ({ shareLink, onClose }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(shareLink);
    alert("Link copied to clipboard!");
  };

  return (
    <div className="fixed top-0 left-0 w-full h-full flex justify-center items-center bg-black bg-opacity-50">
      <div className="bg-white p-4 rounded-lg shadow-lg w-96">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold">Share Post</h2>
          <button onClick={onClose}>
            <FaTimes className="text-gray-600" />
          </button>
        </div>
        <div className="mt-3 flex items-center bg-gray-100 p-2 rounded">
          <input
            type="text"
            value={shareLink}
            readOnly
            className="w-full bg-transparent outline-none"
          />
          <button onClick={handleCopy} className="ml-2 text-blue-500">
            <FaCopy />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ShareBox;
