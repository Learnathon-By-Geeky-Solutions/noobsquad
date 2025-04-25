import React from "react";
import { MapPin } from "lucide-react";
import { Link } from "react-router-dom";

const EventCard = ({ event }) => {
    console.log("event:", event);

  return (
    <div className="bg-white p-4 h-fit rounded-2xl shadow-md hover:shadow-lg transition">
        {event.image_url && (
        <img
          src={event.image_url || "default-image.png"}
          alt="Event"
          className="w-full h-44 object-cover rounded-lg mt-2"
        />
      )}
      <h3 className="text-lg font-semibold mt-2">{event.title}</h3>
      <p className="text-sm text-gray-600">{new Date(event.event_datetime).toLocaleString()}</p>
      
      <p className="text-sm mt-2">{event.description?.slice(0, 100)}...</p>
      <div className="flex items-center">
            <MapPin className="w-4 h-4 mr-1 text-blue-500" />
            <span>{event.location}</span>
        </div>
        <div className="mt-4 text-right">
        <Link
          to={`${event.id}`}
          className="text-sm font-medium text-blue-600 hover:underline"
        >
          See Details →
        </Link>
      </div>

        
    </div>
    

  );
};

export default EventCard;