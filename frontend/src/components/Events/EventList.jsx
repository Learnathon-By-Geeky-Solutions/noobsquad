import { useState, useEffect } from "react";
import api from "../../api"; // Your custom axios API instance
import { ThumbsUp, UserPlus, UserCheck, MapPin, MessageCircleHeart, HeartOff, Heart, Check } from "lucide-react"; // Importing Lucide icons
import { Link } from "react-router-dom";

const EventList = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState({}); // Track loading state for each event
  const [rsvpStatus, setRsvpStatus] = useState({}); // Track RSVP status for each event
  const [currentUserId, setCurrentUserId] = useState(null); // Store the current user's ID

  // Fetch the current user's ID and then fetch events and attendees
  useEffect(() => {
    const fetchUserAndEvents = async () => {
      try {
        // Step 1: Fetch the current user's ID
        const userResponse = await api.get("/auth/users/me/");
        const userId = userResponse.data.id; // Assuming the response contains an "id" field
        setCurrentUserId(userId);

        // Step 2: Fetch all events
        const eventsResponse = await api.get("posts/events/");
        const fetchedEvents = eventsResponse.data;
        setEvents(fetchedEvents);

        // Step 3: Fetch attendees for each event to determine user's RSVP status
        const rsvpData = {};
        await Promise.all(
          fetchedEvents.map(async (event) => {
            try {
              const attendeesResponse = await api.get(`/interactions/event/${event.id}/attendees`);
              const attendees = attendeesResponse.data;

              // Check if the current user has RSVP'd
              const userRsvp = attendees.find((attendee) => attendee.user_id === userId);
              rsvpData[event.id] = {
                interested: userRsvp?.status === "interested" || false,
                going: userRsvp?.status === "going" || false,
              };
            } catch (err) {
              console.error(`Error fetching attendees for event ${event.id}:`, err);
              rsvpData[event.id] = { interested: false, going: false }; // Default to false on error
            }
          })
        );

        setRsvpStatus(rsvpData);
      } catch (err) {
        setError("Error fetching user, events, or attendees.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserAndEvents();
  }, []);

  // Function to handle RSVP (mark or unmark)
  const handleRSVP = async (eventId, status, isUnmarking = false) => {
    if (!currentUserId) {
      alert("User ID not available. Please try again later.");
      return;
    }

    setActionLoading((prev) => ({ ...prev, [eventId]: true }));
    try {
      if (isUnmarking) {
        // Unmark RSVP
        await api.delete(`/interactions/event/${eventId}/rsvp`);
        alert(`You have successfully unmarked your ${status} status!`);
      } else {
        // Mark RSVP
        await api.post(`/interactions/event/${eventId}/rsvp`, {
          event_id: eventId,
          status: status,
        });
        alert(`You have successfully marked yourself as ${status}!`);
      }

      // Refetch attendees to update RSVP status
      const attendeesResponse = await api.get(`/interactions/event/${eventId}/attendees`);
      const attendees = attendeesResponse.data;
      const userRsvp = attendees.find((attendee) => attendee.user_id === currentUserId);

      setRsvpStatus((prev) => ({
        ...prev,
        [eventId]: {
          ...prev[eventId],
          interested: userRsvp?.status === "interested" || false,
          going: userRsvp?.status === "going" || false,
        },
      }));
    } catch (err) {
      console.error(`Error ${isUnmarking ? "unmarking" : "marking"} as ${status}:`, err);
      alert(`Failed to ${isUnmarking ? "unmark" : "mark"} as ${status}. Please try again.`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [eventId]: false }));
    }
  };

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="max-w-full mx-auto grid grid-cols-1 sm:grid-cols-2 gap-2 mt-10">
      {events.length > 0 ? (
        events.map((event) => {
          const eventRsvp = rsvpStatus[event.id] || {};
          const isInterested = eventRsvp.interested || false;
          const isGoing = eventRsvp.going || false;

          return (
            <div
              className="bg-white bg-black/5 rounded-lg shadow-sm overflow-hidden transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-xl"
            >
              <img
                src="https://via.placeholder.com/400"
                alt={event.title}
                className="w-full h-32 object-cover rounded-t-lg"
              />
              <div className="p-3">
                <div className="flex justify-between items-center">
                <Link
              to={`/dashboard/events/${event.id}`}
              key={event.id}
              className="block"
            >
                  <h2 className="text-sm font-semibold text-gray-900">{event.title}</h2>

                </Link>
                  {event.event_datetime === new Date().toISOString().split("T")[0] ? (
                    <span className="bg-red-500 text-white text-xs font-bold py-1 px-2 rounded-full">
                      Happening now
                    </span>
                  ) : (
                    <span className="text-xs text-gray-600">
                      {new Date(event.event_datetime).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-700 mt-2">{event.description}</p>

                <div className="flex justify-between items-center mt-3 text-xs text-gray-800">
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-1 text-blue-500" />
                    <span>{event.location}</span>
                  </div>
                </div>

                {/* Event Actions */}
                <div className="flex space-x-3 mt-3">
                  <button
                    onClick={() =>
                      handleRSVP(event.id, "interested", isInterested)
                    }
                    disabled={actionLoading[event.id]}
                    className={`w-full flex items-center justify-center py-1 px-3 bg-blue-500 text-white rounded-lg transition-all duration-300 text-xs ${
                      actionLoading[event.id]
                        ? "opacity-50 cursor-not-allowed"
                        : isInterested
                        ? "hover:bg-blue-700"
                        : "hover:bg-blue-600"
                    }`}
                  >
                    {isInterested ? (
                      <Check className="w-4 h-4 mr-2" />
                    ) : (
                      <ThumbsUp className="w-4 h-4 mr-2" />
                    )}
                    
                    {actionLoading[event.id]
                      ? "Processing..."
                      : isInterested
                      ? ""
                      : "Interested"}
                  </button>
                  <button
                    onClick={() => handleRSVP(event.id, "going", isGoing)}
                    disabled={actionLoading[event.id]}
                    className={`w-full flex items-center justify-center py-1 px-3 bg-gray-600 text-white rounded-lg transition-all duration-300 text-xs ${
                      actionLoading[event.id]
                        ? "opacity-50 cursor-not-allowed"
                        : isGoing
                        ? "hover:bg-gray-800"
                        : "hover:bg-gray-700"
                    }`}
                  >
                    {isGoing ? (
                      <UserCheck className="w-4 h-4 mr-2" />
                    ) : (
                      <UserPlus className="w-4 h-4 mr-2" />
                    )}
                    {actionLoading[event.id]
                      ? "Processing..."
                      : isGoing
                      ? ""
                      : "Going"}
                  </button>
                </div>
              </div>
            </div>
          );
        })
      ) : (
        <p className="text-gray-700">No events available.</p>
      )}
    </div>
  );
};

export default EventList;