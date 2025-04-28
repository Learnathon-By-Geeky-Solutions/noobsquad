import { useState, useEffect } from "react";
import api from "../../api";
import { ThumbsUp, UserPlus, UserCheck, MapPin, Check, Calendar, Clock } from "lucide-react";
import { Link } from "react-router-dom";

const EventList = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState({ message: "", type: "" });
  const [actionLoading, setActionLoading] = useState({});
  const [rsvpStatus, setRsvpStatus] = useState({});
  const [currentUserId, setCurrentUserId] = useState(null);

  const fetchAttendeesForEvent = async (eventId, userId) => {
    try {
      const attendeesResponse = await api.get(`/interactions/event/${eventId}/attendees`);
      const attendees = attendeesResponse.data;
      const userRsvp = attendees.find((attendee) => attendee.user_id === userId);
      return {
        interested: userRsvp?.status === "interested" || false,
        going: userRsvp?.status === "going" || false,
      };
    } catch (err) {
      console.error(`Error fetching attendees for event ${eventId}:`, err);
      return { interested: false, going: false };
    }
  };

  useEffect(() => {
    const fetchUserAndEvents = async () => {
      try {
        const userResponse = await api.get("/auth/users/me/");
        const userId = userResponse.data.id;
        setCurrentUserId(userId);

        const eventsResponse = await api.get("posts/events/");
        const fetchedEvents = eventsResponse.data;
        setEvents(fetchedEvents);

        const rsvpData = {};
        await Promise.all(
          fetchedEvents.map(async (event) => {
            rsvpData[event.id] = await fetchAttendeesForEvent(event.id, userId);
          })
        );

        setRsvpStatus(rsvpData);
      } catch (err) {
        if (err.response) {
          // Server responded with an error
          if (err.response.status === 401) {
            setError({ 
              type: "auth",
              message: "Please log in to view events." 
            });
          } else if (err.response.status === 404) {
            setError({ 
              type: "notFound",
              message: "There are no Events available" 
            });
          } else {
            setError({ 
              type: "server",
              message: "Server error. Please try again later." 
            });
          }
        } else if (err.request) {
          // Request made but no response
          setError({ 
            type: "network",
            message: "Network error. Please check your connection." 
          });
        } else {
          setError({ 
            type: "unknown",
            message: "An unexpected error occurred. Please try again." 
          });
        }
        console.error("Error details:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserAndEvents();
  }, []);

  const handleRSVP = async (eventId, status, isUnmarking = false) => {
    if (!currentUserId) {
      alert("User ID not available. Please try again later.");
      return;
    }

    setActionLoading((prev) => ({ ...prev, [eventId]: true }));
    try {
      if (isUnmarking) {
        await api.delete(`/interactions/event/${eventId}/rsvp`);
        alert(`You have successfully unmarked your ${status} status!`);
      } else {
        await api.post(`/interactions/event/${eventId}/rsvp`, {
          event_id: eventId,
          status: status,
        });
        alert(`You have successfully marked yourself as ${status}!`);
      }

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

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800">Upcoming Events</h2>
        <Link
          to="/dashboard/events"
          className="text-blue-600 hover:text-blue-800 flex items-center gap-2 text-sm font-medium transition-colors duration-200"
        >
          <span>View all events</span>
          <span aria-hidden="true" className="text-lg">&rarr;</span>
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-100 border-t-blue-500 mx-auto mb-6"></div>
            <p className="text-gray-600 font-medium">Loading exciting events...</p>
          </div>
        </div>
      ) : error.message ? (
        <div className={`p-8 rounded-xl text-center ${getErrorStyles(error.type)}`}>
          <p className="font-medium text-lg mb-4">{error.message}</p>
          {error.type === 'network' && (
            <button 
              onClick={() => window.location.reload()} 
              className="text-sm px-6 py-2.5 bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors duration-200 font-medium"
            >
              Try Again
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {events.length > 0 ? (
            events.slice(0, 4).map((event) => {
              const eventRsvp = rsvpStatus[event.id] || {};
              const isInterested = eventRsvp.interested || false;
              const isGoing = eventRsvp.going || false;
              const eventDate = new Date(event.event_datetime);
              const isToday = eventDate.toDateString() === new Date().toDateString();

              return (
                <div
                  key={event.id}
                  className="group bg-white rounded-lg shadow-sm overflow-hidden transition-all duration-300 ease-in-out hover:shadow-md border border-gray-100 flex flex-col max-w-sm"
                >
                  <div className="relative h-32">
                    <img
                      src={event.image_url || "https://via.placeholder.com/400"}
                      alt={event.title}
                      className="w-full h-32 object-cover"
                    />
                    {isToday && (
                      <div className="absolute top-2 right-2">
                        <span className="bg-red-500 text-white text-xs font-bold py-1 px-2 rounded-full">
                          Today
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="p-3 flex-1 flex flex-col">
                    <Link
                      to={`/dashboard/events/${event.id}`}
                      className="block group"
                    >
                      <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors duration-200 mb-2 line-clamp-1">
                        {event.title}
                      </h3>
                    </Link>

                    <div className="space-y-1.5 mb-2">
                      <div className="flex items-center text-gray-600">
                        <Calendar className="w-4 h-4 mr-1.5 text-blue-500 flex-shrink-0" />
                        <span className="text-xs">
                          {eventDate.toLocaleDateString(undefined, { 
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      </div>
                      <div className="flex items-center text-gray-600">
                        <Clock className="w-4 h-4 mr-1.5 text-blue-500 flex-shrink-0" />
                        <span className="text-xs">
                          {eventDate.toLocaleTimeString(undefined, { 
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>
                      <div className="flex items-center text-gray-600">
                        <MapPin className="w-4 h-4 mr-1.5 text-blue-500 flex-shrink-0" />
                        <span className="text-xs line-clamp-1">{event.location}</span>
                      </div>
                    </div>

                    <p className="text-xs text-gray-600 line-clamp-2 mb-3">
                      {event.description}
                    </p>

                    <div className="flex gap-2 mt-auto">
                      <button
                        onClick={() => handleRSVP(event.id, "interested", isInterested)}
                        disabled={actionLoading[event.id]}
                        className={`flex-1 flex items-center justify-center py-1 px-2 rounded text-xs font-medium transition-all duration-200 ${
                          isInterested
                            ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        } ${actionLoading[event.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        {isInterested ? (
                          <>
                            <Check className="w-3 h-3 mr-1" />
                            Interested
                          </>
                        ) : (
                          <>
                            <ThumbsUp className="w-3 h-3 mr-1" />
                            Interested
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => handleRSVP(event.id, "going", isGoing)}
                        disabled={actionLoading[event.id]}
                        className={`flex-1 flex items-center justify-center py-1 px-2 rounded text-xs font-medium transition-all duration-200 ${
                          isGoing
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-gray-800 text-white hover:bg-gray-900'
                        } ${actionLoading[event.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        {isGoing ? (
                          <>
                            <UserCheck className="w-3 h-3 mr-1" />
                            Going
                          </>
                        ) : (
                          <>
                            <UserPlus className="w-3 h-3 mr-1" />
                            Going
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-2 bg-gray-50 rounded-2xl p-12 text-center">
              <div className="text-gray-400 mb-4">
                <Calendar className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-gray-900 text-xl font-semibold mb-2">No events available</h3>
              <p className="text-gray-600">Check back later for upcoming events!</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const getErrorStyles = (errorType) => {
  switch (errorType) {
    case 'network':
      return 'bg-yellow-50 text-yellow-700 border border-yellow-200';
    case 'auth':
      return 'bg-blue-50 text-blue-700 border border-blue-200';
    default:
      return 'bg-red-50 text-red-700 border border-red-200';
  }
};

export default EventList;