import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProfileCompletion from '../pages/ProfileCompletion';

// Mock useAuth
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
  }),
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

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('ProfileCompletion Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      })
    );
  });

  const renderProfileCompletion = () =>
    render(
      <MemoryRouter>
        <ProfileCompletion />
      </MemoryRouter>
    );

  const completeStep1 = async () => {
    fireEvent.change(screen.getByPlaceholderText('University Name'), {
      target: { value: 'University A' },
    });
    fireEvent.change(screen.getByPlaceholderText('Department'), {
      target: { value: 'Computer Science' },
    });
    fireEvent.click(screen.getByText('Machine Learning'));
    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(screen.getByText('Step 2: Upload Profile Picture (Optional)')).toBeInTheDocument();
    });
  };

  it('renders the profile completion form with step 1', () => {
    renderProfileCompletion();

    expect(screen.getByPlaceholderText('University Name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Department')).toBeInTheDocument();
    expect(screen.getByText('Select Fields of Interest')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('displays an error for missing fields when Next is clicked', async () => {
    renderProfileCompletion();

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('University Name')).toHaveClass('error');
      expect(screen.getByPlaceholderText('Department')).toHaveClass('error');
      expect(screen.getByText('Select Fields of Interest')).toHaveClass('error-text');
    });
  });

  it('moves to step 2 after valid inputs', async () => {
    renderProfileCompletion();

    await completeStep1();
  });

  it('uploads a profile picture on step 2', async () => {
    renderProfileCompletion();

    // Complete Step 1
    await completeStep1();

    // Step 2
    const file = new File(['dummy content'], 'profile.jpg', { type: 'image/jpeg' });
    const input = screen.getByLabelText('Drag or Drop Your Profile Picture');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Finish'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profile/upload_picture'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer mock-token',
          }),
        })
      );
    });
  });

  it('skips the profile picture upload if not selected', async () => {
    renderProfileCompletion();

    // Complete Step 1
    await completeStep1();

    // Step 2
    fireEvent.click(screen.getByText('Skip'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      expect(global.fetch).toHaveBeenCalledTimes(1); // Only step 1 call
    });
  });

  it('navigates to dashboard after skipping profile picture', async () => {
    renderProfileCompletion();

    // Complete Step 1
    await completeStep1();

    // Step 2
    fireEvent.click(screen.getByText('Skip'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});