import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useParams } from 'react-router-dom';
import SharePost from '../pages/SharedPost'; // Adjust path as needed
import api from '../api/axios';

// Mock axios
vi.mock('../api/axios', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

describe('SharePost Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderSharePost = (shareToken) => {
    useParams.mockReturnValue({ shareToken });
    return render(
      <MemoryRouter initialEntries={[`/share/${shareToken}`]}>
        <SharePost />
      </MemoryRouter>
    );
  };

  it('renders loading state initially', () => {
    api.get.mockReturnValue(new Promise(() => {})); // Unresolved promise to stay in loading state
    renderSharePost('abc123');

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    api.get.mockRejectedValueOnce(new Error('Not found'));
    renderSharePost('invalid-token');

    await waitFor(() => {
      expect(screen.getByText('Post not found or link is invalid.')).toBeInTheDocument();
      expect(screen.getByText('Post not found or link is invalid.')).toHaveClass('text-red-500');
    });
  });

  it('renders post title and content when API call succeeds', async () => {
    const mockPost = {
      title: 'Test Post Title',
      content: 'This is the test post content.',
    };
    api.get.mockResolvedValueOnce({ data: mockPost });
    renderSharePost('valid-token');

    await waitFor(() => {
      expect(screen.getByText('Test Post Title')).toBeInTheDocument();
      expect(screen.getByText('This is the test post content.')).toBeInTheDocument();
    });

    const titleElement = screen.getByText('Test Post Title');
    const contentElement = screen.getByText('This is the test post content.');
    expect(titleElement).toHaveClass('text-xl');
    expect(titleElement).toHaveClass('font-bold');
    expect(contentElement).toHaveClass('mt-2');
    expect(contentElement).toHaveClass('text-gray-700');
    expect(screen.getByRole('heading', { level: 2 })).toBe(titleElement);
  });

  it('calls API with correct shareToken', async () => {
    const mockPost = { title: 'Test Post', content: 'Test Content' };
    api.get.mockResolvedValueOnce({ data: mockPost });
    renderSharePost('xyz789');

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/interactions/share/xyz789');
      expect(screen.getByText('Test Post')).toBeInTheDocument();
    });
  });
});