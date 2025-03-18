import React from "react";
import PropTypes from "prop-types";

// ✅ Reusable Form Container
export const FormContainer = ({ title, children }) => (
  <div className="bg-white shadow-md rounded-lg p-6">
    <h2 className="text-xl font-semibold mb-4">{title}</h2>
    {children}
  </div>
);

FormContainer.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

// ✅ Reusable Text Input
export const TextInput = ({ placeholder, value, onChange }) => (
  <input
    type="text"
    placeholder={placeholder}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    required
    className="w-full border p-2 rounded"
  />
);

TextInput.propTypes = {
  placeholder: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

// ✅ Reusable Text Area
export const TextArea = ({ placeholder, value, onChange }) => (
  <textarea
    placeholder={placeholder}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    required
    className="w-full border p-2 rounded"
  />
);

TextArea.propTypes = {
  placeholder: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

// ✅ Reusable Submit Button
export const SubmitButton = ({ text, onClick, disabled }) => (
  <button
    type="button"
    onClick={onClick}
    className={`w-full text-white font-bold py-2 px-4 rounded ${
      disabled ? "bg-gray-400 cursor-not-allowed" : "bg-blue-500 hover:bg-blue-600"
    }`}
    disabled={disabled}
  >
    {text}
  </button>
);

SubmitButton.propTypes = {
  text: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
};

// ✅ Paper Card Component
export const PaperCard = ({ paper }) => (
  <li className="p-4 border rounded shadow-md bg-white">
    <h3 className="text-lg font-semibold text-gray-900">{paper.title}</h3>
    <p className="text-gray-700"><strong>Field:</strong> {paper.research_field}</p>
    <p className="text-gray-600">{paper.details}</p>
  </li>
);

PaperCard.propTypes = {
  paper: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    research_field: PropTypes.string.isRequired,
    details: PropTypes.string.isRequired,
  }).isRequired,
};

// ✅ Collaboration Request Card
export const RequestCard = ({ req }) => (
  <li className="p-4 border rounded shadow-md bg-white">
    <strong className="text-gray-900">{req.requester_username}</strong> sent you a collaboration request
    <p className="text-gray-700">
      <strong>Message:</strong> {req.message}
    </p>
  </li>
);

RequestCard.propTypes = {
  req: PropTypes.shape({
    id: PropTypes.number.isRequired,
    requester_username: PropTypes.string.isRequired,
    message: PropTypes.string.isRequired,
  }).isRequired,
};
