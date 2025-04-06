import { useState, useEffect } from "react";
import api from "../../api"; // Your custom axios API instance
import { ThumbsUp, UserPlus } from "lucide-react"; // Importing Lucide icons

const EventList = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        // Fetch the event data
        const response = await api.get("posts/events/"); // Adjust the URL if needed
        setEvents(response.data);
      } catch (err) {
        setError("Error fetching events.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="max-w-full mx-auto grid grid-cols-1 sm:grid-cols-2 gap-4 mt-10">
      {events.length > 0 ? (
        events.map((event) => (
          <div
            key={event.id}
            className="bg-white bg-black/10 rounded-lg shadow-sm overflow-hidden transition-all duration-300 ease-in-out transform hover:scale-105 hover:shadow-xl"
          >
            <img
              src="https://via.placeholder.com/400" // Replace with event's actual image URL
              alt={event.title}
              className="w-full h-32 object-cover rounded-t-lg" // Adjusted height for smaller image
            />
            <div className="p-3">
              <div className="flex justify-between items-center">
                <h2 className="text-sm font-semibold text-gray-900">{event.title}</h2>
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
                  <ThumbsUp className="w-4 h-4 mr-1 text-blue-500" />
                  <span>{event.interested} Interested</span>
                </div>
                <div className="flex items-center">
                  <UserPlus className="w-4 h-4 mr-1 text-green-500" />
                  <span>{event.going} Going</span>
                </div>
              </div>

              {/* Event Actions */}
              <div className="flex space-x-3 mt-3">
                <button className="w-full flex items-center justify-center py-1 px-3 bg-blue-500 text-white rounded-lg transition-all duration-300 hover:bg-blue-600 text-xs">
                  <ThumbsUp className="w-4 h-4 mr-2" /> Interested
                </button>
                <button className="w-full flex items-center justify-center py-1 px-3 bg-gray-600 text-white rounded-lg transition-all duration-300 hover:bg-gray-700 text-xs">
                  <UserPlus className="w-4 h-4 mr-2" /> Going
                </button>
              </div>
            </div>
          </div>
        ))
      ) : (
        <p className="text-gray-700">No events available.</p>
      )}
    </div>
  );
};

export default EventList;