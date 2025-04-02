import { vi } from 'vitest';
import { signup, login, fetchUser } from '../../api/auth'; // Adjust path as needed
import api from '../../api/axios';

// Mock the axios instance
vi.mock('../../api/axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('auth.js', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null); // Default: no token
  });

  describe('signup', () => {
    it('should make a POST request to the signup endpoint and return the response', async () => {
      const mockUserData = { username: 'testuser', email: 'test@example.com', password: 'password123' };
      const mockResponse = { data: { message: 'Signup successful' } };

      api.post.mockResolvedValueOnce(mockResponse);

      const response = await signup(mockUserData);

      expect(api.post).toHaveBeenCalledWith('/auth/signup/', mockUserData);
      expect(response).toEqual(mockResponse);
    });

    it('should throw an error if the signup fails', async () => {
      const mockUserData = { username: 'testuser', email: 'test@example.com', password: 'password123' };
      const mockError = new Error('Signup failed');

      api.post.mockRejectedValueOnce(mockError);

      await expect(signup(mockUserData)).rejects.toThrow('Signup failed');
    });
  });

  describe('login', () => {
    it('should successfully login and store the token in localStorage', async () => {
      const mockCredentials = { username: 'testuser', password: 'password123' };
      const mockResponse = { data: { access_token: 'mocked_token' } };

      api.post.mockResolvedValueOnce(mockResponse);

      const response = await login(mockCredentials);

      const expectedFormData = new URLSearchParams({
        username: 'testuser',
        password: 'password123',
      });
      expect(api.post).toHaveBeenCalledWith(
        '/auth/token',
        expectedFormData,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'mocked_token');
      expect(response).toEqual(mockResponse.data);
    });

    it('should throw an error if no token is received from the backend', async () => {
      const mockCredentials = { username: 'testuser', password: 'password123' };
      const mockResponse = { data: {} };

      api.post.mockResolvedValueOnce(mockResponse);

      await expect(login(mockCredentials)).rejects.toThrow('No access_token received from backend');
    });

    it('should throw an error if login fails', async () => {
      const mockCredentials = { username: 'testuser', password: 'password123' };
      const mockError = new Error('Login failed');

      api.post.mockRejectedValueOnce(mockError);

      await expect(login(mockCredentials)).rejects.toThrow('Login failed');
    });
  });

  describe('fetchUser', () => {
    it('should successfully fetch the user data if token exists', async () => {
      const mockToken = 'mocked_token';
      const mockResponse = { data: { username: 'testuser', email: 'test@example.com' } };

      localStorageMock.getItem.mockReturnValue(mockToken);
      api.get.mockResolvedValueOnce(mockResponse);

      const response = await fetchUser();

      expect(api.get).toHaveBeenCalledWith('/auth/users/me/', {
        headers: { Authorization: `Bearer ${mockToken}` },
      });
      expect(response).toEqual(mockResponse.data);
    });

    it('should throw an error if no token is found in localStorage', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await expect(fetchUser()).rejects.toThrow('No token found');
    });

    it('should throw an error if fetching user fails', async () => {
      const mockToken = 'mocked_token';
      const mockError = new Error('Failed to fetch user');

      localStorageMock.getItem.mockReturnValue(mockToken);
      api.get.mockRejectedValueOnce(mockError);

      await expect(fetchUser()).rejects.toThrow('Failed to fetch user');
    });
  });
});