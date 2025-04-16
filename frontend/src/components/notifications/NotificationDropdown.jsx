import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TimeAgo } from '../../utils/TimeUtils';
import PropTypes from 'prop-types';

const NotificationDropdown = ({ userId, onRead }) => {
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();

  const fetchNotifications = async () => {
    try {
      if (!userId) return;
      const response = await fetch(`http://localhost:8000/notifications?user_id=${userId}`);
      const data = await response.json();
      setNotifications(data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const markAsRead = async (notifId) => {
    try {
      await fetch(`http://localhost:8000/notifications/${notifId}/read`, {
        method: 'PUT',
      });
      fetchNotifications();
      onRead();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [userId]);

  const handleNotificationClick = (postId, notifId) => {
    markAsRead(notifId);
    navigate(`/dashboard/posts?highlight=${postId}`);
  };

  const formatNotifType = (type) => {
    return type?.replace(/_/g, ' ');
  };

  const getNotificationMessage = (notif, actorUsername) => {
    const notifType = formatNotifType(notif.type);
    switch (notifType) {
      case 'comment':
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> commented on your post
          </>
        );
      case 'like':
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> liked your post
          </>
        );
      case 'share':
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> shared your post
          </>
        );
      case 'new post':
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> posted a new post
          </>
        );
      case 'reply':
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> replied to your comment
          </>
        );
      default:
        return (
          <>
            <span className="font-semibold">{actorUsername}</span> did something
          </>
        );
    }
  };

  return (
    <div className="absolute right-0 mt-2 w-80 bg-white shadow-lg border rounded-md z-50 max-h-96 overflow-y-auto">
      <h3 className="p-4 text-lg font-bold border-b text-gray-500 text-center">Notifications</h3>

      {notifications.length === 0 ? (
        <p className="p-4 text-gray-500">No notifications</p>
      ) : (
        notifications.map((notif) => (
          <button
            key={notif.id}
            onClick={() => handleNotificationClick(notif.post_id, notif.id)}
            type="button"
            className={`flex w-full items-center gap-3 p-3 border-b cursor-pointer transition-all relative hover:bg-gray-50 ${
              notif.is_read ? 'bg-white text-gray-600' : 'bg-blue-50 text-gray-800'
            }`}
            aria-label={`Notification about post ${notif.post_id}`}
          >
            {/* Avatar */}
            <img
              src={notif.actor_image_url || "/default-avatar.png"}
              alt={notif.actor_username}
              className="w-10 h-10 rounded-full object-cover flex-shrink-0"
            />

            {/* Notification text and time */}
            <div className="flex-1 flex flex-col">
              <div className="text-sm">{getNotificationMessage(notif, notif.actor_username)}</div>
              <div className="text-xs text-gray-400 mt-1 self-end">
                {TimeAgo(notif.created_at)}
              </div>
            </div>

            {/* Unread indicator */}
            {!notif.is_read && (
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 absolute top-3 right-3"></span>
            )}
          </button>
        ))
      )}
    </div>
  );
};

NotificationDropdown.propTypes = {
  userId: PropTypes.number.isRequired,
  onRead: PropTypes.func.isRequired,
};

export default NotificationDropdown;