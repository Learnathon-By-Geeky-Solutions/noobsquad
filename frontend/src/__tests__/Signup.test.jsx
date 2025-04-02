import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import Signup from '../pages/Signup'; // Adjust path as needed
import * as authApi from '../api/auth';
import { ChatProvider } from '../context/ChatContext';

// Mock the auth API functions
vi.mock('../api/auth', () => ({
  signup: vi.fn(),
}));

// Mock Navbar component
vi.mock('../components/Navbar', () => ({
  default: () => <div data-testid="navbar">Navbar</div>,
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

describe('Signup Component', () => {
  const mockSignup = authApi.signup;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderSignup = () =>
    render(
      <MemoryRouter initialEntries={['/signup']}>
        <ChatProvider>
          <Signup />
        </ChatProvider>
      </MemoryRouter>
    );

  it('renders the Signup form', () => {
    renderSignup();

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
  });

  it('displays an error message if signup fails', async () => {
    mockSignup.mockRejectedValueOnce(new Error('Signup failed'));

    renderSignup();

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'testuser' },
    });
    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'testuser@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Sign Up' }));

    await waitFor(() => {
      expect(screen.getByText('Signup failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('navigates to the login page on successful signup', async () => {
    mockSignup.mockResolvedValueOnce({ data: {} });

    renderSignup();

    fireEvent.change(screen.getByPlaceholderText('Username'), {
      target: { value: 'testuser' },
    });
    fireEvent.change(screen.getByPlaceholderText('Email'), {
      target: { value: 'testuser@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('Password'), {
      target: { value: 'password123' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Sign Up' }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('disables the submit button while loading', async () => {
    let resolveSignup;
    mockSignup.mockImplementation(() => new Promise((resolve) => { resolveSignup = resolve; }));

    renderSignup();

    const usernameInput = screen.getByPlaceholderText('Username');
    const emailInput = screen.getByPlaceholderText('Email');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign Up' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(emailInput, { target: { value: 'testuser@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(submitButton.textContent).toBe('Signing up...');
    }, { timeout: 1000 });

    resolveSignup({ data: {} });
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
      expect(submitButton.textContent).toBe('Sign Up');
    });
  });
});