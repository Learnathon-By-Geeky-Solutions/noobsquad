import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../../api";
import { MapPin, Clock, AlertCircle, Users } from "lucide-react"; // Added Users for attendee count

const EventDetails = () => {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rsvpStatus, setRsvpStatus] = useState(null);
  const [rsvpCounts, setRsvpCounts] = useState({ going: 0, interested: 0 });

  useEffect(() => {
    const fetchEventDetails = async () => {
      try {
        const [eventRes, statusRes, countRes] = await Promise.all([
          api.get(`/posts/events/?event_id=${eventId}`),
          api.get(`/interactions/event/${eventId}/my_rsvp/`),
          api.get(`/interactions/posts/events/rsvp/counts/?event_id=${eventId}`)
        ]);
        setEvent(eventRes.data);
        console.log("event:", eventRes.data)
        setRsvpStatus(statusRes.data.status);
        setRsvpCounts(countRes.data);
      } catch (err) {
        setError("Failed to fetch event details.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEventDetails();
  }, [eventId]);

  const handleRSVP = async (status) => {
    try {
      const token = localStorage.getItem("token");
      await api.post(`/interactions/event/${eventId}/rsvp`, {
        event_id: eventId,
        status,
        headers: { Authorization: `Bearer ${token}` }
      });
      setRsvpStatus(status);

      // Refresh counts
      const countRes = await api.get(`/interactions/posts/events/rsvp/counts/?event_id=${eventId}`);
      setRsvpCounts(countRes.data);
    } catch (err) {
      console.error("Failed to update RSVP:", err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "long" });
    const year = date.getFullYear();
    const ordinalSuffix = (n) =>
      ["th", "st", "nd", "rd"][(n % 10 <= 3 && Math.floor(n / 10) !== 1) ? n % 10 : 0];
    return `${day}${ordinalSuffix(day)} ${month}, ${year}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <span className="text-xl text-gray-700">Loading event details...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <AlertCircle className="w-6 h-6 text-red-600 mr-2" />
        <span className="text-red-600">{error}</span>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <span className="text-gray-700">No event found!</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 md:mt-20">
      {/* Cover Photo */}
      <div className="relative">
        <img
          src={event.image_url || "https://via.placeholder.com/1200x400"}
          alt={event.title}
          className="w-full h-80 object-cover"
        />
        {/* Event Title Overlay */}
        <div className="absolute bottom-0 left-0 p-6 bg-gradient-to-t from-black/60 to-transparent w-full">
          <h1 className="text-3xl md:text-4xl font-bold text-white">{event.title}</h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto -mt-16 px-4 md:mt-5">
        {/* Card Container */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Event Actions (RSVP Buttons) */}
          {/* RSVP Buttons */}
          <div className="p-4 border-b border-gray-200 flex space-x-4">
            <button
              onClick={() => handleRSVP("going")}
              className={`px-4 py-2 rounded-md font-semibold transition ${
                rsvpStatus === "going"
                  ? "bg-blue-700 text-white"
                  : "bg-gray-200 text-gray-800 hover:bg-gray-300"
              }`}
            >
              Going
            </button>
            <button
              onClick={() => handleRSVP("interested")}
              className={`px-4 py-2 rounded-md font-semibold transition ${
                rsvpStatus === "interested"
                  ? "bg-blue-700 text-white"
                  : "bg-gray-200 text-gray-800 hover:bg-gray-300"
              }`}
            >
              Interested
            </button>
            <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md font-semibold hover:bg-gray-300 transition">
              Share
            </button>
          </div>

          {/* Event Details */}
          <div className="p-6">
            {/* Date and Time */}
            <div className="flex items-center mb-4">
              <Clock className="w-5 h-5 text-gray-500 mr-2" />
              <span className="text-gray-800 font-medium">
                {formatDate(event.event_datetime)} at{" "}
                {new Date(event.event_datetime).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>

            {/* Location */}
            <div className="flex items-center mb-4">
              <MapPin className="w-5 h-5 text-gray-500 mr-2" />
              <span className="text-gray-800">{event.location}</span>
            </div>

            {/* Attendees Placeholder */}
            <div className="flex items-center mb-6">
              <Users className="w-5 h-5 text-gray-500 mr-2" />
              <span className="text-gray-600">{rsvpCounts.going} people going • {rsvpCounts.interested} interested</span>
              {/* Replace X and Y with actual data if available */}
            </div>

            {/* Description */}
            <div className="border-t border-gray-200 pt-4">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">About This Event</h2>
              <p className="text-gray-700">{event.description}</p>
            </div>
          </div>
        </div>

        {/* Tabs Placeholder (Optional) */}
        <div className="mt-6 bg-white rounded-lg shadow-md p-4">
          <div className="flex space-x-6 border-b border-gray-200">
            <button className="pb-2 text-blue-600 border-b-2 border-blue-600 font-semibold">
              Details
            </button>
            <button className="pb-2 text-gray-600 hover:text-blue-600">Discussion</button>
            <button className="pb-2 text-gray-600 hover:text-blue-600">More</button>
          </div>
          {/* Add content for tabs here if implementing */}
        </div>
      </div>
    </div>
  );
};

export default EventDetails;