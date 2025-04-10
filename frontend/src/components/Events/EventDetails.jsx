import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../../api"; // Your custom axios API instance

const EventDetails = () => {
  const { eventId } = useParams(); // Get eventId from URL parameters
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEventDetails = async () => {
      try {
        // Modified endpoint to match typical REST API pattern
        const response = await api.get(`/posts/events/?event_id=${eventId}`);
        setEvent(response.data);
      } catch (err) {
        setError("Failed to fetch event details.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEventDetails();
  }, [eventId]);

  if (loading) {
    return <div className="text-center">Loading event details...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg md:mt-24 mt-10">
      <h2 className="text-3xl font-bold mb-4">{event.title}</h2>
      <p className="text-xl mb-4">{new Date(event.event_datetime).toLocaleDateString()}</p>
      <p className="text-lg text-gray-700">{event.description}</p>
      <div className="mt-4 text-gray-600">
        <p><strong>Location:</strong> {event.location}</p>
        {/* Add more details as needed */}
      </div>
    </div>
  );
};

export default EventDetails;