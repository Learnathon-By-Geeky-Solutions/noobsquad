import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import NotificationDropdown from './NotificationDropdown';

const NotificationBell = ({ userId }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const fetchUnreadCount = async () => {
    if (!userId) return; // ✅ Prevent call if userId is undefined
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/notifications/unread?user_id=${userId}`);
      const data = await res.json();
      setUnreadCount(data.length);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  };
  useEffect(() => {
    fetchUnreadCount();
  }, [userId]);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className="relative"
      >
        <span className="material-icons">Notifications</span>
        {unreadCount > 0 && (
          <span className="absolute -top-2 -right-2 bg-red-600 text-white text-xs rounded-full px-2 py-0.5">
            {unreadCount}
          </span>
        )}
      </button>

      {dropdownOpen && (
        <NotificationDropdown userId={userId} onRead={fetchUnreadCount} />
      )}
    </div>
  );
};
NotificationBell.propTypes = {
  userId: PropTypes.string.isRequired,
};


export default NotificationBell;
