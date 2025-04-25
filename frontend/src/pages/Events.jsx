// src/components/events/EventsPage.jsx
import React, { useEffect, useState } from "react";
import api from "../api";
import GroupedEventsSection from "../components/EventGroup";

const EventsPage = () => {
  const [groupedEvents, setGroupedEvents] = useState({
    within_7_days: [],
    within_30_days: [],
    within_year: []
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGroupedIds = async () => {
      try {
        const res = await api.get("/top/events/grouped-by-time");
        console.log("fetched id:", res.data);
        setGroupedEvents(res.data);
      } catch (err) {
        console.error("Failed to fetch grouped event IDs:", err);
      }
      setLoading(false);
    };

    fetchGroupedIds();
  }, []);

  if (loading) return <div className="text-center py-8">Loading events...</div>;

  return (
    <div className="px-4 md:px-12 py-8 mt-20 md:mt-24">
      <GroupedEventsSection
        title="Events Within 7 Days"
        eventIds={groupedEvents.within_7_days}
      />
      <GroupedEventsSection
        title="Events Within 30 Days"
        eventIds={groupedEvents.within_30_days}
      />
      <GroupedEventsSection
        title="Events Within This Year"
        eventIds={groupedEvents.within_year}
      />
    </div>
  );
};

export default EventsPage;
