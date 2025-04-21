
import axios from 'axios';
import { forgotPassword } from '../auth';




jest.mock("axios");

describe('forgotPassword() forgotPassword method', () => {
  const apiUrl = 'http://localhost:8000/auth/forgot-password/';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Happy paths', () => {
    it('should send a POST request with the correct data', async () => {
      // Arrange
      const data = { email: 'test@example.com' };
      axios.post.mockResolvedValue({ data: { success: true } });

      // Act
      const response = await forgotPassword(data);

      // Assert
      expect(axios.post).toHaveBeenCalledWith(apiUrl, data);
      expect(response.data.success).toBe(true);
    });

    it('should handle a successful response correctly', async () => {
      // Arrange
      const data = { email: 'user@example.com' };
      const mockResponse = { data: { message: 'Password reset link sent' } };
      axios.post.mockResolvedValue(mockResponse);

      // Act
      const response = await forgotPassword(data);

      // Assert
      expect(response).toEqual(mockResponse);
    });
  });

  describe('Edge cases', () => {
    it('should handle network errors gracefully', async () => {
      // Arrange
      const data = { email: 'error@example.com' };
      const errorMessage = 'Network Error';
      axios.post.mockRejectedValue(new Error(errorMessage));

      // Act & Assert
      await expect(forgotPassword(data)).rejects.toThrow(errorMessage);
    });

    it('should handle server errors correctly', async () => {
      // Arrange
      const data = { email: 'servererror@example.com' };
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal Server Error' },
        },
      };
      axios.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(forgotPassword(data)).rejects.toEqual(mockError);
    });

    it('should handle invalid email format', async () => {
      // Arrange
      const data = { email: 'invalid-email' };
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Invalid email format' },
        },
      };
      axios.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(forgotPassword(data)).rejects.toEqual(mockError);
    });

    it('should handle empty email input', async () => {
      // Arrange
      const data = { email: '' };
      const mockError = {
        response: {
          status: 400,
          data: { error: 'Email is required' },
        },
      };
      axios.post.mockRejectedValue(mockError);

      // Act & Assert
      await expect(forgotPassword(data)).rejects.toEqual(mockError);
    });
  });
});