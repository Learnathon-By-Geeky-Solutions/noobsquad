import { useState } from "react";
import api from "../../api"; // Importing your custom API instance

const CreateEventForm = () => {
  const [eventTitle, setEventTitle] = useState("");
  const [eventDescription, setEventDescription] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [eventTime, setEventTime] = useState("");
  const [userTimezone, setUserTimezone] = useState("Asia/Dhaka");
  const [location, setLocation] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("content", content);
    formData.append("event_title", eventTitle);
    formData.append("event_description", eventDescription);
    formData.append("event_date", eventDate);
    formData.append("event_time", eventTime);
    formData.append("user_timezone", userTimezone);
    formData.append("location", location);

    try {
      // Send POST request with FormData directly (no need to set Content-Type header manually)
      const response = await api.post("posts/create_event_post/", formData, { 
        headers: { "Content-Type": "multipart/form-data" },
    });

      const data = await response.data;
      alert("Event created successfully!");
      window.location.reload();
      console.log(data);
    } catch (err) {
      setError("An error occurred while creating the event.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-md shadow-md mt-10 md:mt-24">
      <h2 className="text-2xl font-semibold mb-4">Create Event Post</h2>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="eventTitle" className="block text-sm font-medium text-gray-700">
            Event Title
          </label>
          <input
            type="text"
            id="eventTitle"
            className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
            value={eventTitle}
            onChange={(e) => setEventTitle(e.target.value)}
            required
          />
        </div>

        <div className="mb-4">
          <label htmlFor="eventDescription" className="block text-sm font-medium text-gray-700">
            Event Description
          </label>
          <textarea
            id="eventDescription"
            className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
            value={eventDescription}
            onChange={(e) => setEventDescription(e.target.value)}
            required
          />
        </div>

        <div className="mb-4 flex gap-4">
          <div>
            <label htmlFor="eventDate" className="block text-sm font-medium text-gray-700">
              Event Date
            </label>
            <input
              type="date"
              id="eventDate"
              className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="eventTime" className="block text-sm font-medium text-gray-700">
              Event Time
            </label>
            <input
              type="time"
              id="eventTime"
              className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
              value={eventTime}
              onChange={(e) => setEventTime(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="mb-4">
          <label htmlFor="location" className="block text-sm font-medium text-gray-700">
            Location
          </label>
          <input
            type="text"
            id="location"
            className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="content" className="block text-sm font-medium text-gray-700">
            Content (Optional)
          </label>
          <textarea
            id="content"
            className="mt-1 p-2 block w-full border border-gray-300 rounded-md"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
        </div>

        <div className="flex justify-center mb-4">
          <button
            type="submit"
            className={`py-2 px-4 bg-blue-500 text-white rounded-md ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
            disabled={loading}
          >
            {loading ? "Creating..." : "Create Event"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateEventForm;
