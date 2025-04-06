import React, { useState } from 'react';
import { Search as SearchIcon } from 'lucide-react';
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
    <div className="p-4 max-w-lg mx-auto md:mt-24">
      <form onSubmit={handleSearch} className="flex items-center">
        <input
          type="text"
          placeholder="Search..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="border border-gray-300 rounded-l-lg p-2 flex-grow focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          className="bg-blue-500 text-white p-2 rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <SearchIcon className="w-5 h-5" />
        </button>
      </form>

      {error && <div className="text-red-500 mt-4">{error}</div>}

      {results && (
        <div className="mt-4 space-y-4">
          <div>
            <h3 className="text-lg font-semibold">Connections</h3>
            {results.connections?.length > 0 ? (
              results.connections.map((connection) => (
                <div key={connection.id} className="p-4 border rounded-lg">
                  <p>ID: {connection.id}</p>
                  <p>User ID: {connection.user_id}</p>
                  <p>Friend ID: {connection.friend_id}</p>
                  <p>Status: {connection.status}</p>
                </div>
              ))
            ) : (
              <p>No connections found.</p>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold">Posts</h3>
            {results.posts?.length > 0 ? (
              results.posts.map((post) => (
                <div key={post.id} className="p-4 border rounded-lg">
                  <p>ID: {post.id}</p>
                  <p>User ID: {post.user_id}</p>
                  <p>Content: {post.content}</p>
                  <p>Post Type: {post.post_type}</p>
                  <p>Created At: {post.created_at}</p>
                  <p>Likes: {post.like_count}</p>
                </div>
              ))
            ) : (
              <p>No posts found.</p>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold">Events</h3>
            {results.events?.length > 0 ? (
              results.events.map((event) => (
                <div key={event.id} className="p-4 border rounded-lg">
                  <p>ID: {event.id}</p>
                  <p>User ID: {event.user_id}</p>
                  <p>Title: {event.title}</p>
                  <p>Description: {event.description}</p>
                  <p>Location: {event.location}</p>
                </div>
              ))
            ) : (
              <p>No events found.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Search;
