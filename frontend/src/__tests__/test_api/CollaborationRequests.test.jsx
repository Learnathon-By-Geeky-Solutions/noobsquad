import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CollaborationRequests from '../../api/CollaborationRequests'; // Adjust path as needed
import api from '../../api';

vi.mock('../../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('CollaborationRequests Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.alert globally
    global.alert = vi.fn(); // Directly mock window.alert
  });

  const renderComponent = () =>
    render(
      <MemoryRouter>
        <CollaborationRequests />
      </MemoryRouter>
    );

  it('renders loading state initially', () => {
    api.get.mockReturnValue(new Promise(() => {})); // Keeps the loading state
    renderComponent();

    // Use a test ID to find the loader component
    expect(screen.getByTestId('loader')).toBeInTheDocument(); // Ensures loader is rendered
  });

  it('displays error message when no requests are found', async () => {
    api.get.mockResolvedValueOnce({ data: [] });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('No pending collaboration requests.')).toBeInTheDocument();
    });
  });

  it('displays error message when API call fails', async () => {
    api.get.mockRejectedValueOnce(new Error('Fetch failed'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Error fetching collaboration requests.')).toBeInTheDocument();
    });
  });

  it('renders collaboration requests when data is returned', async () => {
    const mockRequests = [
      {
        id: 1,
        requester_username: 'user1',
        sender_avatar: '/avatar1.png',
        research_title: 'Project A',
        message: 'Please collaborate with me!',
        timestamp: '2023-10-01T12:00:00Z',
      },
      {
        id: 2,
        requester_username: 'user2',
        research_title: 'Project B',
        message: 'Interested in this project.',
        timestamp: '2023-10-02T14:00:00Z',
      },
    ];
    api.get.mockResolvedValueOnce({ data: mockRequests });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Collaboration Requests')).toBeInTheDocument();
      expect(screen.getByText('user1')).toBeInTheDocument();

      // Now we're only checking the project titles and messages, not the full phrase
      expect(screen.getByText('Project A')).toBeInTheDocument(); // Ensure the project title is displayed
      expect(screen.getByText('"Please collaborate with me!"')).toBeInTheDocument();
      expect(screen.getByText(/Oct 1, 2023/i)).toBeInTheDocument();

      expect(screen.getByText('user2')).toBeInTheDocument();
      expect(screen.getByText('Project B')).toBeInTheDocument(); // Ensure the project title is displayed
      expect(screen.getByText('"Interested in this project."')).toBeInTheDocument();
      expect(screen.getByText(/Oct 2, 2023/i)).toBeInTheDocument();
    });
  });

  it('triggers message action with username', async () => {
    const mockRequests = [
      { id: 1, requester_username: 'user1', research_title: 'Project A', message: 'Join me!' },
    ];
    api.get.mockResolvedValueOnce({ data: mockRequests });
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('user1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Message'));

    // Ensure the correct username is passed
    expect(global.alert).toHaveBeenCalledWith('Messaging user1 (Coming soon...)');
  });

  // Additional tests to ensure accept and decline actions work
  it('handles accept action and removes request from list', async () => {
    const mockRequests = [
      { id: 1, requester_username: 'user1', research_title: 'Project A', message: 'Join me!' },
    ];
    api.get.mockResolvedValueOnce({ data: mockRequests });
    api.post.mockResolvedValueOnce({});
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('user1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Accept'));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/research/accept-collaboration/1/');
      expect(screen.queryByText('user1')).not.toBeInTheDocument();
    });
  });

  it('shows alert on accept failure', async () => {
    const mockRequests = [
      { id: 1, requester_username: 'user1', research_title: 'Project A', message: 'Join me!' },
    ];
    api.get.mockResolvedValueOnce({ data: mockRequests });
    api.post.mockRejectedValueOnce(new Error('Accept failed'));
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('user1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Accept'));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Failed to accept request. Please try again.');
      expect(screen.getByText('user1')).toBeInTheDocument(); // Request remains
    });
  });
});
