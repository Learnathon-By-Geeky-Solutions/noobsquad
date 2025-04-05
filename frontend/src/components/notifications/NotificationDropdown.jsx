import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TimeAgo } from '../../utils/TimeUtils';


const NotificationDropdown = ({ userId, onRead }) => {
  const [notifications, setNotifications] = useState([]);
  const navigate = useNavigate();  // Initialize useNavigate hook


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
      fetchNotifications(); // Refresh notifications
      onRead(); // Update unread count
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };



  useEffect(() => {
    fetchNotifications();
  }, [userId]); // Refresh when userId changes

  const handleNotificationClick = (postId, notifId) => {
    markAsRead(notifId); // Mark the notification as read
    navigate(`/dashboard/posts?highlight=${postId}`);
  };

  const formatNotifType = (type) => {
    return type?.replace(/_/g, ' '); // Replace all underscores with space
  };

  const getNotificationMessage = (notif, actorUsername) => {
    const notiftype = formatNotifType(notif.type);
    switch (notiftype) {
      case 'comment':
        return `${actorUsername} commented on your post`;
      case 'like':
        return `${actorUsername} liked on your post`;
      case 'share':
        return `${actorUsername} shared your post`;
      case 'new post':
        return `${actorUsername} posted a new post`;
      case 'reply':
        return `${actorUsername} replied to your comment`;       
      default:
        return `${actorUsername} did something`;
    }
  };

  return (
    <div className="absolute right-0 mt-2 w-80 bg-white shadow-lg border rounded-md z-50 max-h-96 overflow-y-auto">
      <h3 className="p-4 text-lg font-bold border-b text-gray-500 text-center">Notifications</h3>
  
      {notifications.length === 0 ? (
        <p className="p-4 text-gray-500">No notifications</p>
      ) : (
        notifications.map((notif) => (
          <div
            key={notif.id}
            onClick={() => handleNotificationClick(notif.post_id, notif.id)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                handleNotificationClick(notif.post_id, notif.id);
              }
            }}
            tabIndex={0} // Makes the div focusable for keyboard navigation
            role="button" // Indicates that this element acts like a button
            aria-label={`Notification about post ${notif.post_id}`} // Describes the action for screen readers
            className={`flex items-start gap-3 p-3 border-b cursor-pointer transition-all relative hover:bg-gray-50 ${
              notif.is_read ? 'bg-white text-gray-600' : 'bg-blue-50 text-gray-800'
            }`}
          >
            {/* Notification content here */}
          
            {/* Avatar */}
            <img
              src={notif.actor_image_url || "/default-avatar.png"} // fallback image
              alt={notif.actor_username}
              className="w-10 h-10 rounded-full object-cover"
            />
  
            {/* Notification text and time */}
            <div className="flex-1">
              <div className="text-sm">{getNotificationMessage(notif, notif.actor_username)}</div>
              <div className="text-xs text-right text-gray-400 mt-1">
                {TimeAgo(notif.created_at)}
              </div>
            </div>
  
            {/* Unread indicator */}
            {!notif.is_read && (
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 absolute top-3 right-3"></span>
            )}
          </div>
        ))
      )}
    </div>
  );
  
};

export default NotificationDropdown;
