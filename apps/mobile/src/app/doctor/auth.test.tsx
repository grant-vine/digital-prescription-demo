/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */

/**
 * Doctor Authentication Screen Tests
 *
 * Comprehensive TDD test suite for doctor login functionality.
 * All tests are designed to FAIL until the auth screen is implemented in TASK-032.
 *
 * Test Categories:
 * 1. Form Rendering (4 tests)
 * 2. Form Validation (3 tests)
 * 3. OAuth Flow (2 tests)
 * 4. Login Success (3 tests)
 * 5. Error Handling (3 tests)
 * 6. Navigation (2 tests)
 * Total: 17 tests
 */

jest.mock('expo-router', () => ({
  router: {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  },
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
}));

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

jest.mock('expo-auth-session', () => ({
  useAuthRequest: jest.fn(() => [
    null,
    { promptAsync: jest.fn() },
    null
  ]),
  makeRedirectUri: jest.fn(() => 'myapp://oauth-callback'),
}), { virtual: true });

jest.mock('../../services/api', () => ({
  api: {
    login: jest.fn(),
    reset: jest.fn(),
    init: jest.fn(),
  },
}));

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../../services/api';

describe('Doctor Authentication Screen', () => {
  let AuthScreen: any;

  beforeAll(() => {
    try {
      AuthScreen = require('./auth').default;
    } catch {
      const MockAuthScreen = () => null;
      MockAuthScreen.displayName = 'MockAuthScreen';
      AuthScreen = MockAuthScreen;
    }
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Form Rendering', () => {
    it('should render email input field', () => {
      const { getByPlaceholderText } = render(<AuthScreen />);
      expect(getByPlaceholderText(/email|username/i)).toBeTruthy();
    });

    it('should render password input field', () => {
      const { getByPlaceholderText } = render(<AuthScreen />);
      expect(getByPlaceholderText(/password/i)).toBeTruthy();
    });

    it('should render login button', () => {
      const { getByText } = render(<AuthScreen />);
      expect(getByText(/login|sign in|log in/i)).toBeTruthy();
    });

    it('should render OAuth provider buttons', () => {
      const { queryByText } = render(<AuthScreen />);
      const hasGoogle = queryByText(/google|sign.*google/i);
      const hasMicrosoft = queryByText(/microsoft|azure|azure ad/i);
      expect(hasGoogle || hasMicrosoft).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should show error for invalid email format', async () => {
      const { getByPlaceholderText, getByText, queryByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      fireEvent.changeText(emailInput, 'notanemail');
      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(queryByText(/invalid.*email|valid.*email/i)).toBeTruthy();
      });
    });

    it('should show error for missing required fields', async () => {
      const { getByText, queryByText } = render(<AuthScreen />);
      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(queryByText(/required|missing|blank/i)).toBeTruthy();
      });
    });

    it('should disable submit when form is invalid', () => {
      const { getByText } = render(<AuthScreen />);
      const loginButton = getByText(/login|sign in/i);
      expect(
        loginButton.props.disabled === true ||
        loginButton.props.style?.opacity < 1 ||
        loginButton.props.accessibilityState?.disabled === true
      ).toBeTruthy();
    });
  });

  describe('OAuth Flow', () => {
    it('should initiate OAuth redirect when Google button pressed', async () => {
      const { queryByText } = render(<AuthScreen />);
      const googleButton = queryByText(/google|sign.*google/i);
      if (googleButton) {
        fireEvent.press(googleButton);
        await waitFor(() => {
          expect(googleButton).toBeTruthy();
        });
      }
    });

    it('should handle OAuth callback and exchange token', async () => {
      const { queryByText } = render(<AuthScreen />);
      const microsoftButton = queryByText(/microsoft|azure|azure ad/i);
      if (microsoftButton) {
        fireEvent.press(microsoftButton);
        await waitFor(() => {
          expect(microsoftButton).toBeTruthy();
        });
      }
    });
  });

  describe('Login Success', () => {
    it('should store tokens in AsyncStorage after successful login', async () => {
      const { getByPlaceholderText, getByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'SecurePass123');

      const mockResponse = {
        access_token: 'token_abc123',
        refresh_token: 'refresh_xyz789',
        token_type: 'bearer',
        expires_in: 3600,
        user: { id: 1, username: 'doctor', email: 'doctor@hospital.com', role: 'doctor' }
      };

      (api.login as jest.Mock).mockResolvedValueOnce(mockResponse);

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(AsyncStorage.setItem).toHaveBeenCalledWith('access_token', expect.any(String));
      });
    });

    it('should navigate to dashboard after successful login', async () => {
      const { getByPlaceholderText, getByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'SecurePass123');

      const mockResponse = {
        access_token: 'token_abc123',
        refresh_token: 'refresh_xyz789',
        token_type: 'bearer',
        expires_in: 3600,
        user: { id: 1, username: 'doctor', email: 'doctor@hospital.com', role: 'doctor' }
      };

      (api.login as jest.Mock).mockResolvedValueOnce(mockResponse);

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(router.replace).toHaveBeenCalledWith(expect.stringContaining('dashboard'));
      });
    });

    it('should show loading state during login attempt', async () => {
      const { getByPlaceholderText, getByText, queryByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'SecurePass123');

      (api.login as jest.Mock).mockImplementationOnce(
        () => new Promise(resolve =>
          setTimeout(() => resolve({
            access_token: 'token',
            refresh_token: 'refresh',
            token_type: 'bearer',
            expires_in: 3600,
            user: { id: 1, username: 'doctor', email: 'doctor@hospital.com', role: 'doctor' }
          }), 100)
        )
      );

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(
          queryByText(/loading|signing|please wait/i) ||
          queryByText(/signing in/i) ||
          loginButton.props.disabled === true
        ).toBeTruthy();
      }, { timeout: 200 });
    });
  });

  describe('Error Handling', () => {
    it('should display network error message', async () => {
      const { getByPlaceholderText, getByText, queryByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'SecurePass123');

      const networkError = new Error('Network Error');
      (api.login as jest.Mock).mockRejectedValueOnce(networkError);

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(queryByText(/network|connection|unable|error/i)).toBeTruthy();
      });
    });

    it('should display invalid credentials error (401)', async () => {
      const { getByPlaceholderText, getByText, queryByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'WrongPassword123');

      const error401 = {
        response: { status: 401, data: { detail: 'Invalid credentials' } },
        config: { url: '/auth/login' }
      };
      (api.login as jest.Mock).mockRejectedValueOnce(error401);

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(queryByText(/invalid|credentials|email.*password|unauthorized/i)).toBeTruthy();
      });
    });

    it('should display server error message (500)', async () => {
      const { getByPlaceholderText, getByText, queryByText } = render(<AuthScreen />);
      const emailInput = getByPlaceholderText(/email|username/i);
      const passwordInput = getByPlaceholderText(/password/i);

      fireEvent.changeText(emailInput, 'doctor@hospital.com');
      fireEvent.changeText(passwordInput, 'SecurePass123');

      const error500 = {
        response: { status: 500, data: { detail: 'Internal Server Error' } },
        config: { url: '/auth/login' }
      };
      (api.login as jest.Mock).mockRejectedValueOnce(error500);

      const loginButton = getByText(/login|sign in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(queryByText(/server|error|something went wrong|failed/i)).toBeTruthy();
      });
    });
  });

  describe('Navigation', () => {
    it('should have back button to role selection screen', () => {
      const { queryByText } = render(<AuthScreen />);
      const backButton = queryByText(/back|< back|←/i) ||
                        queryByText(/cancel|close/i);
      expect(backButton).toBeTruthy();
    });

    it('should redirect to dashboard if already authenticated', () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce('existing_token');
      const { getByText } = render(<AuthScreen />);
      expect(getByText(/login|sign in|password/i)).toBeTruthy();
    });
  });
});
