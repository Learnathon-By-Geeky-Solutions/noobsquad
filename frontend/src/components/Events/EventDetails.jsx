import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../../api"; // Your custom axios API instance
import { MapPin, Clock, AlertCircle } from "lucide-react"; // Lucide icons for location, time, and error

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

  const formatDate = (dateString) => {
    const date = new Date(dateString);

    // Get the day of the month
    const day = date.getDate();

    // Get the month and convert it to a string (e.g., "April")
    const month = date.toLocaleString("default", { month: "long" });

    // Get the year
    const year = date.getFullYear();

    // Add the ordinal suffix (e.g., "st", "nd", "rd", "th")
    const ordinalSuffix = (n) => {
      const suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"];
      return n % 10 <= 3 && Math.floor(n / 10) !== 1 ? suffix[n % 10] : suffix[0];
    };

    // Combine the formatted date
    return `${day}${ordinalSuffix(day)} ${month}, ${year}`;
  };

  if (loading) {
    return (
      <div className="text-center flex items-center justify-center h-screen">
        <span className="text-2xl">Loading event details...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 flex items-center justify-center h-screen">
        <AlertCircle className="w-6 h-6 mr-2" />
        <span>{error}</span>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="text-center text-gray-700">
        <span>No event found!</span>
      </div>
    );
  }

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100 md:mt-20">
      <div className="max-w-4xl w-full p-8 bg-white rounded-xl shadow-2xl transform transition-all duration-300 ease-in-out hover:scale-105 hover:shadow-xl">
        {/* Page Name: "Event Details" */}
        <h2 className="text-5xl text-gray-900 text-center mb-8">Event Details</h2>

        {/* Event Title */}
        <div className="text-center mb-6">
          <h2 className="text-4xl font-extrabold text-gray-900 mb-4">{event.title}</h2>
        </div>

        {/* Event Image */}
        <div className="mb-6">
          <img
            src={event.image_url || "https://via.placeholder.com/600"} // Use a default image if no image URL is provided
            alt={event.title}
            className="w-full h-64 object-cover rounded-lg shadow-md"
          />
        </div>

        {/* Event Time */}
        <div className="flex justify-center items-center mb-6">
          <Clock className="w-6 h-6 text-gray-500" />
          <p className="text-lg text-gray-700">
            {new Date(event.event_datetime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </p>
        </div>

        {/* Event Date */}
        <p className="text-xl text-gray-800 mb-6 text-center">
          {formatDate(event.event_datetime)} {/* Using the custom formatDate function */}
        </p>

        {/* Event Description */}
        <p className="text-lg text-gray-700 mb-6 text-center">{event.description}</p>

        {/* Event Location */}
        <div className="flex justify-center items-center text-gray-600 mt-4">
          <MapPin className="w-5 h-5 text-blue-500 mr-2" />
          <p className="text-lg">{event.location}</p>
        </div>
      </div>
    </div>
  );
};

export default EventDetails;
