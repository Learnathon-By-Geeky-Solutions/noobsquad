import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import FetchUserPapers from '../../api/FetchUserPapers'; // Adjust path as needed
import api from '../../api'; // Matches the component's import
import { BrowserRouter as Router, useNavigate } from 'react-router-dom';

// Mock the api module
vi.mock('../../api', () => ({
  default: {
    get: vi.fn(),
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

describe('FetchUserPapers Component', () => {
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

  it('shows loading state initially', async () => {
    api.get.mockImplementationOnce(() =>
      new Promise((resolve) => setTimeout(() => resolve({ data: [] }), 100))
    );

    render(
      <Router>
        <FetchUserPapers />
      </Router>
    );

    expect(screen.getByText('My current works (Ongoing)')).toBeInTheDocument();
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();

    await waitFor(
      () => expect(api.get).toHaveBeenCalledTimes(1),
      { timeout: 200 }
    );
  });

  it('shows error message when API call fails', async () => {
    api.get.mockRejectedValueOnce(new Error('Network Error'));

    render(
      <Router>
        <FetchUserPapers />
      </Router>
    );

    await waitFor(
      () => expect(screen.getByText('Error fetching your research papers.')).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('shows no papers message when API returns empty data', async () => {
    api.get.mockResolvedValueOnce({ data: [] });

    render(
      <Router>
        <FetchUserPapers />
      </Router>
    );

    await waitFor(
      () => expect(screen.getByText('No research papers found.')).toBeInTheDocument(),
      { timeout: 1000 }
    );
  });

  it('renders the list of papers correctly when API returns data', async () => {
    const mockPapers = [
      { id: 1, title: 'Paper 1', research_field: 'Physics', details: 'Details about paper 1' },
      { id: 2, title: 'Paper 2', research_field: 'Biology', details: 'Details about paper 2' },
    ];
    api.get.mockResolvedValueOnce({ data: mockPapers });

    render(
      <Router>
        <FetchUserPapers />
      </Router>
    );

    await waitFor(
      () => {
        expect(screen.getByText('Paper 1')).toBeInTheDocument();
        expect(screen.getByText('Paper 2')).toBeInTheDocument();
        expect(screen.getByText((content, element) => 
          element?.textContent === 'Field: Physics'
        )).toBeInTheDocument();
        expect(screen.getByText((content, element) => 
          element?.textContent === 'Details: Details about paper 1'
        )).toBeInTheDocument();
        expect(screen.getByText((content, element) => 
          element?.textContent === 'Field: Biology'
        )).toBeInTheDocument();
        expect(screen.getByText((content, element) => 
          element?.textContent === 'Details: Details about paper 2'
        )).toBeInTheDocument();
      },
      { timeout: 1000 }
    );
  });

  it('redirects to login page when unauthorized (401)', async () => {
    const mockNavigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);

    api.get.mockRejectedValueOnce({ response: { status: 401 } });

    render(
      <Router>
        <FetchUserPapers />
      </Router>
    );

    await waitFor(
      () => {
        expect(mockAlert).toHaveBeenCalledWith('Unauthorized! Please log in.');
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      },
      { timeout: 1000 }
    );
  });
});