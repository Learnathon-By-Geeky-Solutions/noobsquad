// src/components/events/GroupedEventsSection.jsx
import React, { useEffect, useState } from "react";
import api from "../api";
import EventCard from "./EventCard";

const GroupedEventsSection = ({ title, eventIds }) => {
  const [events, setEvents] = useState([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const LIMIT = offset === 0 ? 4 : 8;

  const fetchEvents = async () => {
    if (!eventIds.length) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      eventIds.slice(offset, offset + LIMIT).forEach(id => params.append("event_ids", id));
      params.append("offset", 0);
      params.append("limit", eventIds.length); // we'll slice manually

      const res = await api.get(`/top/events/by-ids/paginated?${params}`);
      const newEvents = res.data;
      setEvents(prev => [...prev, ...newEvents]);
      setOffset(prev => prev + LIMIT);
      if (offset + LIMIT >= eventIds.length) setHasMore(false);
    } catch (err) {
      console.error("Error fetching events:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  return (
    <div className="mb-12">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {events.map(event => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>

      {hasMore && (
        <div className="mt-4 text-center">
          <button
            onClick={fetchEvents}
            className="text-blue-500 hover:underline font-medium"
            disabled={loading}
          >
            {loading ? "Loading..." : "See More"}
          </button>
        </div>
      )}
    </div>
  );
};

export default GroupedEventsSection;
