import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // Import fireEvent here
import PostResearch from '../../api/PostResearch'; // Adjust path as needed
import api from '../../api'; // Matches the component's import
import { BrowserRouter as Router, useNavigate } from 'react-router-dom';

// Mock the api module
vi.mock('../../api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Partially mock react-router-dom to preserve BrowserRouter while mocking useNavigate
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: vi.fn(),
  };
});

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Mock window.alert
const mockAlert = vi.fn();
global.alert = mockAlert;

describe('PostResearch Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key) =>
      key === 'token' ? 'mock-token' : null
    );
    mockAlert.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders form correctly', async () => {
    render(
      <Router>
        <PostResearch />
      </Router>
    );

    expect(screen.getByText('Post Research for Collaboration')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Research Field')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Details (describe the research project or idea)')).toBeInTheDocument();
    expect(screen.getByText('Post Research')).toBeInTheDocument();
  });

  it('displays error message when fields are empty', async () => {
    render(
      <Router>
        <PostResearch />
      </Router>
    );

    const submitButton = screen.getByText('Post Research');
    fireEvent.click(submitButton); // Use fireEvent here

    await waitFor(
      () => expect(screen.getByText('All fields are required.')).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('displays loading state during submission', async () => {
    api.post.mockImplementationOnce(() =>
      new Promise((resolve) => setTimeout(() => resolve({ data: {} }), 100))
    );

    render(
      <Router>
        <PostResearch />
      </Router>
    );

    const titleInput = screen.getByPlaceholderText('Title');
    const researchFieldInput = screen.getByPlaceholderText('Research Field');
    const detailsInput = screen.getByPlaceholderText('Details (describe the research project or idea)');
    const submitButton = screen.getByText('Post Research');

    fireEvent.change(titleInput, { target: { value: 'Test Title' } });
    fireEvent.change(researchFieldInput, { target: { value: 'Test Field' } });
    fireEvent.change(detailsInput, { target: { value: 'Test Details' } });

    fireEvent.click(submitButton);

    await waitFor(
      () => expect(screen.getByText('Posting...')).toBeInTheDocument(),
      { timeout: 200 }
    );
  });

  it('shows error message when API call fails', async () => {
    api.post.mockRejectedValueOnce(new Error('Network Error'));

    render(
      <Router>
        <PostResearch />
      </Router>
    );

    const titleInput = screen.getByPlaceholderText('Title');
    const researchFieldInput = screen.getByPlaceholderText('Research Field');
    const detailsInput = screen.getByPlaceholderText('Details (describe the research project or idea)');
    const submitButton = screen.getByText('Post Research');

    fireEvent.change(titleInput, { target: { value: 'Test Title' } });
    fireEvent.change(researchFieldInput, { target: { value: 'Test Field' } });
    fireEvent.change(detailsInput, { target: { value: 'Test Details' } });

    fireEvent.click(submitButton);

    await waitFor(
      () => expect(screen.getByText('Error posting research. Please try again.')).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('redirects to dashboard after successful submission', async () => {
    const mockNavigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);

    api.post.mockResolvedValueOnce({ data: {} });

    render(
      <Router>
        <PostResearch />
      </Router>
    );

    const titleInput = screen.getByPlaceholderText('Title');
    const researchFieldInput = screen.getByPlaceholderText('Research Field');
    const detailsInput = screen.getByPlaceholderText('Details (describe the research project or idea)');
    const submitButton = screen.getByText('Post Research');

    fireEvent.change(titleInput, { target: { value: 'Test Title' } });
    fireEvent.change(researchFieldInput, { target: { value: 'Test Field' } });
    fireEvent.change(detailsInput, { target: { value: 'Test Details' } });

    fireEvent.click(submitButton);

    await waitFor(
      () => {
        expect(mockAlert).toHaveBeenCalledWith('✅ Research posted successfully!');
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard/research/my_post_research_papers');
      },
      { timeout: 1000 }
    );
  });
});
