import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Login from '../pages/Login'; // Adjust the import path as needed
import * as authApi from '../api/auth';
import { ChatProvider } from '../context/ChatContext';

// Mock the auth API functions
vi.mock('../api/auth', () => ({
  login: vi.fn(),
  fetchUser: vi.fn(),
}));

// Mock AuthContext with a proper mock function
const mockAuthLogin = vi.fn();
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: mockAuthLogin,
  }),
}));

// Mock Navbar component
vi.mock('../components/Navbar', () => ({
  default: () => <div data-testid="navbar">Navbar</div>,
}));

// Mock localStorage
const localStorageMock = {
  setItem: vi.fn(),
  getItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Login Component', () => {
  const mockLogin = authApi.login;
  const mockFetchUser = authApi.fetchUser;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLogin = () =>
    render(
      <MemoryRouter>
        <ChatProvider>
          <Login />
        </ChatProvider>
      </MemoryRouter>
    );

  it('renders login form correctly', () => {
    renderLogin();

    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email or phone')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByText('Continue with University mail')).toBeInTheDocument();
    expect(screen.getByText('Keep me logged in')).toBeInTheDocument();
    expect(screen.getByText('Forgot password?')).toBeInTheDocument();
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('updates form data on input change', () => {
    renderLogin();

    const usernameInput = screen.getByPlaceholderText('Email or phone');
    const passwordInput = screen.getByPlaceholderText('Password');

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(usernameInput.value).toBe('testuser');
    expect(passwordInput.value).toBe('password123');
  });

  it('handles successful login', async () => {
    mockLogin.mockResolvedValue({ access_token: 'mock-token' });
    mockFetchUser.mockResolvedValue({ id: '123', username: 'testuser' });

    renderLogin();

    const usernameInput = screen.getByPlaceholderText('Email or phone');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign in' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'mock-token');
      expect(mockFetchUser).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user_id', '123');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('username', 'testuser');
      expect(mockAuthLogin).toHaveBeenCalledWith('mock-token');
      expect(submitButton.textContent).toBe('Sign in');
    });
  });

  it('displays error on login failure', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));

    renderLogin();

    const usernameInput = screen.getByPlaceholderText('Email or phone');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign in' });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument();
      expect(submitButton.textContent).toBe('Sign in');
    });
  });

  it('toggles remember me checkbox', () => {
    renderLogin();

    const checkbox = screen.getByLabelText('Keep me logged in');
    expect(checkbox.checked).toBe(true);

    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(false);

    fireEvent.click(checkbox);
    expect(checkbox.checked).toBe(true);
  });

  it('disables submit button while loading', async () => {
    let resolveLogin;
    mockLogin.mockImplementation(() => new Promise((resolve) => { resolveLogin = resolve; }));

    renderLogin();

    const usernameInput = screen.getByPlaceholderText('Email or phone');
    const passwordInput = screen.getByPlaceholderText('Password');
    const submitButton = screen.getByRole('button', { name: 'Sign in' });

    // Fill in required fields to pass form validation
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    // Wait for the loading state to be reflected in the DOM
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(submitButton.textContent).toBe('Logging in...');
    }, { timeout: 1000 });

    // Resolve the promise and verify the button reverts
    resolveLogin({ access_token: 'mock-token' });
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
      expect(submitButton.textContent).toBe('Sign in');
    });
  });
});