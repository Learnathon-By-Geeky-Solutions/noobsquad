import { useState, useEffect } from 'react';

const EventDetails = ({ eventId }) => {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!eventId) return; // Do nothing if no eventId is provided

    const fetchEvent = async () => {
      try {
        const response = await fetch(`/posts/events/?event_id=${eventId}`);
        if (!response.ok) {
          throw new Error('Event not found');
        }
        const data = await response.json();
        setEvent(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId]);

  if (loading) {
    return <div className="text-center text-xl">Loading...</div>;
  }

  if (error) {
    return <div className="text-center text-xl text-red-500">{error}</div>;
  }

  if (!event) {
    return <div className="text-center text-xl">Event not found</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-4">{event.name}</h2>
      <p className="text-xl mb-2">{event.date}</p>
      <p className="text-gray-600 mb-4">{event.description}</p>
      <div className="flex justify-between items-center">
        <span className="font-semibold">Location: </span>
        <span>{event.location}</span>
      </div>
    </div>
  );
};

export default EventDetails;
