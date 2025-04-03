import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ConnectedUsers from '../../api/ConnectedUsers'; // Adjust path as needed
import axios from 'axios';
import { ChatContext } from '../../context/ChatContext'; // Adjust path as needed

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('ConnectedUsers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key) =>
      key === 'token' ? 'mock-token' : key === 'user_id' ? '1' : null
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows loading state initially', async () => {
    axios.get.mockImplementationOnce(() =>
      new Promise((resolve) =>
        setTimeout(() => resolve({ data: [] }), 100)
      )
    );
    render(
      <ChatContext.Provider value={{ openChat: vi.fn() }}>
        <ConnectedUsers />
      </ChatContext.Provider>
    );
    expect(screen.getByText('Loading your connections...')).toBeInTheDocument();
    await waitFor(
      () => expect(axios.get).toHaveBeenCalledTimes(1),
      { timeout: 200 }
    );
  });

  it('shows error state on API failure', async () => {
    axios.get.mockRejectedValueOnce(new Error('Failed to fetch'));
    render(
      <ChatContext.Provider value={{ openChat: vi.fn() }}>
        <ConnectedUsers />
      </ChatContext.Provider>
    );
    await waitFor(
      () =>
        expect(
          screen.getByText('Failed to load friends. Please try again later.')
        ).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('shows empty state when no friends', async () => {
    axios.get.mockResolvedValueOnce({ data: [] }); // fetchConnectedUsers
    render(
      <ChatContext.Provider value={{ openChat: vi.fn() }}>
        <ConnectedUsers />
      </ChatContext.Provider>
    );
    await waitFor(
      () =>
        expect(
          screen.getByText('You have no connections yet. Try pairing with someone!')
        ).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('renders friends list and handles message button', async () => {
    const mockFriends = [
      { id: 2, username: 'Friend1', profile_picture: 'pic1.jpg' },
      { id: 3, username: 'Friend2', profile_picture: 'pic2.jpg' },
    ];
    axios.get
      .mockResolvedValueOnce({
        data: [
          { user_id: 1, friend_id: 2 },
          { user_id: 1, friend_id: 3 },
        ],
      }) // fetchConnectedUsers
      .mockResolvedValueOnce({ data: mockFriends[0] }) // fetchUserDetails for friend 2
      .mockResolvedValueOnce({ data: mockFriends[1] }); // fetchUserDetails for friend 3

    const openChatMock = vi.fn();
    render(
      <ChatContext.Provider value={{ openChat: openChatMock }}>
        <ConnectedUsers />
      </ChatContext.Provider>
    );

    await waitFor(
      () => {
        expect(screen.getByText('Friend1')).toBeInTheDocument();
        expect(screen.getByText('Friend2')).toBeInTheDocument();
      },
      { timeout: 1000 }
    );

    const buttons = screen.getAllByText('Message');
    expect(buttons).toHaveLength(2);
    fireEvent.click(buttons[0]);
    expect(openChatMock).toHaveBeenCalledWith(mockFriends[0]);
  });
});