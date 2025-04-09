import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Dashboard from '../pages/Dashboard'; // Adjust path as needed
import { useAuth } from '../context/AuthContext';

// Mock useAuth
const mockUser = { id: '123', username: 'testuser' };
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock components
vi.mock('../components/Navbar', () => ({
  default: ({ onLogoutChatClear, onToggleChat }) => (
    <div data-testid="navbar">
      <button onClick={onLogoutChatClear}>Logout</button>
      <button onClick={onToggleChat} data-testid="toggle-chat">
        Toggle Chat
      </button>
    </div>
  ),
}));

vi.mock('../components/ChatSidebar', () => ({
  default: ({ onSelectUser }) => (
    <div data-testid="chat-sidebar">
      <button onClick={() => onSelectUser({ id: '456', name: 'chatUser' })}>
        Select User
      </button>
    </div>
  ),
}));

vi.mock('../components/ChatPopup', () => ({
  default: ({ user, onClose }) => (
    <div data-testid="chat-popup">
      Chat with {user.name}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

vi.mock('../components/SuggestedUsers', () => ({
  default: () => <div data-testid="suggested-users">Suggested Users</div>,
}));

vi.mock('../components/Research', () => ({
  default: () => <div data-testid="research">Research</div>,
}));

vi.mock('../components/Feed', () => ({
  default: () => <div data-testid="home">Home</div>,
}));

vi.mock('../components/AboutMe/AboutMe', () => ({
  default: () => <div data-testid="user-profile">User Profile</div>,
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ user: mockUser }); // Default: authenticated user
  });

  const renderDashboard = (initialPath = '/dashboard') =>
    render(
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/dashboard/*" element={<Dashboard />} />
          <Route path="/login" element={<div data-testid="login">Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

  it('renders Navbar and nested routes when authenticated', () => {
    renderDashboard('/dashboard');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    // Default route doesn't render any specific component unless specified
  });

  it('redirects to login when not authenticated', async () => {
    useAuth.mockReturnValue({ user: null });

    renderDashboard('/dashboard');

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('renders ChatSidebar on /dashboard/chat route', () => {
    renderDashboard('/dashboard/chat');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('chat-sidebar')).toBeInTheDocument();
  });

  it('shows ChatPopup when a user is selected', async () => {
    renderDashboard('/dashboard/chat');

    // Toggle chat visibility to true
    fireEvent.click(screen.getByTestId('toggle-chat'));

    // Select a user
    const selectUserButton = screen.getByText('Select User');
    fireEvent.click(selectUserButton);

    await waitFor(() => {
      expect(screen.getByTestId('chat-popup')).toBeInTheDocument();
      expect(screen.getByText('Chat with chatUser')).toBeInTheDocument();
    });
  });

  it('closes ChatPopup when close button is clicked', async () => {
    renderDashboard('/dashboard/chat');

    // Toggle chat visibility to true
    fireEvent.click(screen.getByTestId('toggle-chat'));

    // Select a user
    fireEvent.click(screen.getByText('Select User'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-popup')).toBeInTheDocument();
    });

    // Close the chat popup
    fireEvent.click(screen.getByText('Close'));

    await waitFor(() => {
      expect(screen.queryByTestId('chat-popup')).not.toBeInTheDocument();
    });
  });

  it('clears selected user on logout', async () => {
    renderDashboard('/dashboard/chat');

    // Toggle chat visibility to true
    fireEvent.click(screen.getByTestId('toggle-chat'));

    // Select a user
    fireEvent.click(screen.getByText('Select User'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-popup')).toBeInTheDocument();
    });

    // Trigger logout
    fireEvent.click(screen.getByText('Logout'));

    await waitFor(() => {
      expect(screen.queryByTestId('chat-popup')).not.toBeInTheDocument();
    });
  });

  it('renders SuggestedUsers on /dashboard/suggested-users route', () => {
    renderDashboard('/dashboard/suggested-users');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('suggested-users')).toBeInTheDocument();
  });

  it('renders Research on /dashboard/research route', () => {
    renderDashboard('/dashboard/research');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('research')).toBeInTheDocument();
  });

  it('renders Home on /dashboard/posts route', () => {
    renderDashboard('/dashboard/posts');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('home')).toBeInTheDocument();
  });

  it('renders UserProfile on /dashboard/AboutMe route', () => {
    renderDashboard('/dashboard/AboutMe');

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('user-profile')).toBeInTheDocument();
  });
});