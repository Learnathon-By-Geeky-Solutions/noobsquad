import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom'; // Add this to wrap the components
import { Handshake, CheckCircle2 } from 'lucide-react';
import RecentPapers, { PaperCard } from '../../api/RecentPapers'; // Ensure this import is correct
import api from '../../api';

// Mock API calls
vi.mock('../../api');

// Mock window.alert globally
beforeEach(() => {
  vi.spyOn(window, 'alert').mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks(); // Restore mocks after each test
});

describe('RecentPapers Component', () => {
  it('should display research papers once data is fetched', async () => {
    const mockPapers = [
      { id: 1, title: 'Paper 1', research_field: 'Field 1', details: 'Details 1' },
      { id: 2, title: 'Paper 2', research_field: 'Field 2', details: 'Details 2' },
    ];

    api.get.mockResolvedValueOnce({ data: mockPapers });

    render(
      <BrowserRouter>
        <RecentPapers />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Paper 1')).toBeInTheDocument();
      expect(screen.getByText('Paper 2')).toBeInTheDocument();
    });
  });

  it('should show a message when no papers are available', async () => {
    api.get.mockResolvedValueOnce({ data: [] });

    render(
      <BrowserRouter>
        <RecentPapers />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No recent papers available.')).toBeInTheDocument();
    });
  });

  it('should handle unauthorized error gracefully', async () => {
    api.get.mockRejectedValueOnce({ response: { status: 401 } });

    render(
      <BrowserRouter>
        <RecentPapers />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Unauthorized! Please log in.');
    });
  });
});

describe('PaperCard Component', () => {
  it('should render paper title', () => {
    const paper = { id: 1, title: 'Test Paper', research_field: 'Science', details: 'Some details', can_request_collaboration: true };
    
    render(
      <BrowserRouter>
        <PaperCard paper={paper} />
      </BrowserRouter>
    );

    expect(screen.getByText('Test Paper')).toBeInTheDocument();
  });

  it('should display "Request Collaboration" button initially', () => {
    const paper = { id: 1, title: 'Test Paper', research_field: 'Science', details: 'Some details', can_request_collaboration: true };

    render(
      <BrowserRouter>
        <PaperCard paper={paper} />
      </BrowserRouter>
    );

    const button = screen.getByRole('button', { name: /Request Collaboration/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it('should display "Request Sent" after clicking the collaboration button', async () => {
    const paper = { id: 1, title: 'Test Paper', research_field: 'Science', details: 'Some details', can_request_collaboration: true };
    api.post.mockResolvedValueOnce({ status: 200 });

    render(
      <BrowserRouter>
        <PaperCard paper={paper} />
      </BrowserRouter>
    );

    const button = screen.getByRole('button', { name: /Request Collaboration/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Request Sent')).toBeInTheDocument();
    });
  });

  it('should handle collaboration request errors gracefully', async () => {
    const paper = { id: 1, title: 'Test Paper', research_field: 'Science', details: 'Some details', can_request_collaboration: true };
    api.post.mockRejectedValueOnce(new Error('Error requesting collaboration.'));

    render(
      <BrowserRouter>
        <PaperCard paper={paper} />
      </BrowserRouter>
    );

    const button = screen.getByRole('button', { name: /Request Collaboration/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Error requesting collaboration.');
    });
  });
});
