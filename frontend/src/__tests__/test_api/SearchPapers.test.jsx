import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchPapers from '../../api/SearchPapers'; // Adjust the import path as needed
import api from '../../api'; // Adjust the import path as needed

// Mock the api module
vi.mock('../../api', () => {
  return {
    default: {
      get: vi.fn(),
    },
  };
});

describe('SearchPapers Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the component correctly', () => {
    render(<SearchPapers />);
    expect(screen.getByText('Search Research Papers')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter keyword (e.g. AI, robotics, healthcare)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument();
  });

  it('shows error message when search is triggered with empty keyword', async () => {
    render(<SearchPapers />);
    const searchButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.click(searchButton);

    expect(screen.getByText('Please enter a keyword to search.')).toBeInTheDocument();
  });

  it('displays loading state when searching', async () => {
    api.get.mockReturnValue(new Promise(() => {}));
    
    render(<SearchPapers />);
    const input = screen.getByPlaceholderText('Enter keyword (e.g. AI, robotics, healthcare)');
    const searchButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.change(input, { target: { value: 'AI' } });
    fireEvent.click(searchButton);

    expect(screen.getByText('Searching...')).toBeInTheDocument();
    expect(searchButton).toBeDisabled();
  });

  it('displays papers when search is successful', async () => {
    const mockPapers = [
      { id: 1, title: 'AI Advances', author: 'John Doe', research_field: 'AI', abstract: 'This is a test abstract about AI.' },
      { id: 2, title: 'Robotics Today', author: 'Jane Smith', research_field: 'Robotics', abstract: 'Robotics research summary.' },
    ];
    api.get.mockResolvedValue({ data: mockPapers });

    render(<SearchPapers />);
    const input = screen.getByPlaceholderText('Enter keyword (e.g. AI, robotics, healthcare)');
    const searchButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.change(input, { target: { value: 'AI' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      // Check for titles (not split, so direct match works)
      expect(screen.getByText('AI Advances')).toBeInTheDocument();
      expect(screen.getByText('Robotics Today')).toBeInTheDocument();
      
      // Custom matcher for "Author: John Doe" (split across elements)
      expect(screen.getByText((content, element) => {
        return element?.textContent === 'Author: John Doe';
      })).toBeInTheDocument();

      // Custom matcher for "Field: Robotics" (split across elements)
      expect(screen.getByText((content, element) => {
        return element?.textContent === 'Field: Robotics';
      })).toBeInTheDocument();
    });
  });

  it('shows "No papers found" message when API returns empty array', async () => {
    api.get.mockResolvedValue({ data: [] });

    render(<SearchPapers />);
    const input = screen.getByPlaceholderText('Enter keyword (e.g. AI, robotics, healthcare)');
    const searchButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.change(input, { target: { value: 'AI' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('No papers found.')).toBeInTheDocument();
    });
  });

  it('shows error message when API call fails', async () => {
    api.get.mockRejectedValue(new Error('Network error'));

    render(<SearchPapers />);
    const input = screen.getByPlaceholderText('Enter keyword (e.g. AI, robotics, healthcare)');
    const searchButton = screen.getByRole('button', { name: 'Search' });

    fireEvent.change(input, { target: { value: 'AI' } });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Error fetching papers. Please try again.')).toBeInTheDocument();
    });
  });

  it('displays initial empty state message', () => {
    render(<SearchPapers />);
    expect(screen.getByText('Start searching to view research papers.')).toBeInTheDocument();
  });
});