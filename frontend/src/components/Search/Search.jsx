import React, { useState } from 'react';
import { Search as SearchIcon, MapPin, Calendar, ThumbsUp, Users} from 'lucide-react';
import api from '../../api';

const Search = () => {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setError('');
    setResults(null);

    try {
      const response = await api.get('/search/search', {
        params: { keyword },
      });
      setResults(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No results found');
      } else {
        setError('An error occurred. Please try again.');
      }
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto md:mt-24">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="flex items-center mb-6">
        <div className="relative flex-grow">
          <input
            type="text"
            placeholder="Search for connections, posts, or events..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-full p-3 pl-10 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
          />
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        </div>
        <button
          type="submit"
          className="ml-2 bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
        >
          <SearchIcon className="w-5 h-5" />
        </button>
      </form>

      {/* Error Message */}
      {error && (
        <div className="text-red-500 mb-6 text-center font-medium">{error}</div>
      )}

      {/* Search Results */}
      {results && (
        <div className="space-y-8">
          {/* Connections Section */}
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Connections</h3>
            {results.connections?.length > 0 ? (
              results.connections.map((connection) => (
                <div
                  key={connection.id}
                  className="p-4 mb-4 bg-white rounded-lg shadow-md hover:shadow-lg transition duration-200"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-700 font-medium">
                        User ID: {connection.user_id}
                      </p>
                      <p className="text-gray-700 font-medium">
                        Friend ID: {connection.friend_id}
                      </p>
                      <p className="text-gray-500">
                        Status:{' '}
                        <span
                          className={
                            connection.status === 'accepted'
                              ? 'text-green-500'
                              : 'text-yellow-500'
                          }
                        >
                          {connection.status === 'accepted' ? 'Friends' : 'Pending'}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 italic">No connections found.</p>
            )}
          </div>

          {/* Posts Section */}
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Posts</h3>
            {results.posts?.length > 0 ? (
              results.posts.map((post) => (
                <div
                  key={post.id}
                  className="p-4 mb-4 bg-white rounded-lg shadow-md hover:shadow-lg transition duration-200"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-gray-800 font-semibold">
                      {post.username || `User ${post.user_id}`}
                    </p>
                    <p className="text-gray-500 text-sm">
                      {new Date(post.created_at).toLocaleString()}
                    </p>
                  </div>
                  <p className="text-gray-700 mt-2">
                    {post.content || 'No content available'}
                  </p>
                  <div className="flex items-center mt-3 space-x-4">
                    <button className="flex items-center text-gray-600 hover:text-blue-500 transition duration-200">
                      <ThumbsUp className="w-4 h-4 mr-1" />
                      {post.like_count} Likes
                    </button>
                    <button className="flex items-center text-gray-600 hover:text-blue-500 transition duration-200">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                        />
                      </svg>
                      Comment
                    </button>
                    <button className="flex items-center text-gray-600 hover:text-blue-500 transition duration-200">
                      <svg
                        className="w-4 h-4 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M15 15l5-5m0 0l-5-5m5 5H9a2 2 0 00-2 2v4a2 2 0 002 2h6"
                        />
                      </svg>
                      Share
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 italic">No posts found.</p>
            )}
          </div>

          {/* Events Section */}
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Events</h3>
            {results.events?.length > 0 ? (
              results.events.map((event) => (
                <div
                  key={event.id}
                  className="p-4 mb-4 bg-white rounded-lg shadow-md hover:shadow-lg transition duration-200"
                >
                  <h4 className="text-lg font-semibold text-gray-800">
                    {event.title}
                  </h4>
                  <p className="text-gray-600 mt-1">{event.description || 'No description available'}</p>
                  <div className="flex items-center mt-2 space-x-4 text-gray-500 text-sm">
                    <div className="flex items-center">
                      <MapPin className="w-4 h-4 mr-1 text-pink-500" />
                      {event.location || 'Location not specified'}
                    </div>
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1 text-blue-500" />
                      {event.event_datetime
                        ? new Date(event.event_datetime).toLocaleString()
                        : 'Date not specified'}
                    </div>
                  </div>
                  <div className="flex items-center mt-3 space-x-3">
                    <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition duration-200 flex items-center">
                      <ThumbsUp className="w-4 h-4 mr-2" />
                      Interested
                    </button>
                    <button className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition duration-200 flex items-center">
                      <Users className="w-4 h-4 mr-2" />
                      Going
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 italic">No events found.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Search;