import { api, LoginRequest, TokenResponse, Prescription, PrescriptionCreate } from './api';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Setup Mocks
jest.mock('axios');
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}));

describe('API Client', () => {
  // Create a mock instance that is a callable function
  const mockAxiosInstance: any = jest.fn();
  
  // Attach methods to the mock instance
  mockAxiosInstance.interceptors = {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  };
  mockAxiosInstance.get = jest.fn();
  mockAxiosInstance.post = jest.fn();
  mockAxiosInstance.put = jest.fn();
  mockAxiosInstance.delete = jest.fn();
  mockAxiosInstance.defaults = { headers: { common: {} } };

  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the mock instance implementation
    (axios.create as jest.Mock).mockReturnValue(mockAxiosInstance);
    
    // Reset api module if needed (or just re-init)
    api.reset();
    api.init();
  });

  describe('Initialization', () => {
    it('should create axios instance with base URL', () => {
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.stringContaining('http'),
          timeout: expect.any(Number),
        })
      );
    });
  });

  describe('Authentication', () => {
    it('should login successfully and store tokens', async () => {
      const loginCreds: LoginRequest = { username: 'doctor', password: 'password' };
      const mockResponse: TokenResponse = {
        access_token: 'acc_123',
        refresh_token: 'ref_123',
        token_type: 'bearer',
        expires_in: 3600,
        user: { id: 1, username: 'doctor', email: 'doc@test.com', role: 'doctor' }
      };

      mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

      const response = await api.login(loginCreds.username, loginCreds.password);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', loginCreds);
      expect(response).toEqual(mockResponse);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('access_token', 'acc_123');
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('refresh_token', 'ref_123');
    });

    it('should handle login failure (401)', async () => {
      const error = {
        response: { status: 401, data: { detail: 'Invalid credentials' } },
        config: { url: '/auth/login' }
      };
      mockAxiosInstance.post.mockRejectedValueOnce(error);

      await expect(api.login('wrong', 'pass')).rejects.toEqual(error);
    });

    it('should logout and clear tokens', async () => {
      mockAxiosInstance.post.mockResolvedValueOnce({ data: { message: 'Logged out' } });

      await api.logout();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/logout');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('Prescriptions', () => {
    it('should list prescriptions', async () => {
      const mockList = {
        items: [{ id: 1, medication_name: 'Aspirin' }],
        total: 1,
        page: 1,
        page_size: 10
      };
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockList });

      const result = await api.getPrescriptions(1, 10);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/prescriptions', { 
        params: { page: 1, page_size: 10 } 
      });
      expect(result).toEqual(mockList);
    });

    it('should get single prescription by ID', async () => {
      const mockPrescription: Prescription = {
        id: 123,
        doctor_id: 1,
        patient_id: 2,
        medication_name: 'Aspirin',
        dosage: '100mg',
        quantity: 30,
        date_issued: '2023-01-01',
        date_expires: '2023-12-31',
        is_repeat: false,
        repeat_count: 0,
        created_at: '2023-01-01',
        updated_at: '2023-01-01'
      };
      mockAxiosInstance.get.mockResolvedValueOnce({ data: mockPrescription });

      const result = await api.getPrescription(123);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/prescriptions/123');
      expect(result).toEqual(mockPrescription);
    });

    it('should handle 404 when getting prescription', async () => {
      const error = {
        response: { status: 404, data: { detail: 'Not found' } },
        config: { url: '/prescriptions/999' }
      };
      mockAxiosInstance.get.mockRejectedValueOnce(error);

      await expect(api.getPrescription(999)).rejects.toEqual(error);
    });

    it('should create prescription', async () => {
      const newRx: PrescriptionCreate = {
        patient_id: 2,
        medication_name: 'Amoxicillin',
        medication_code: 'AMOX-500',
        dosage: '500mg',
        quantity: 21,
        instructions: 'Take 1 capsule 3 times daily',
        date_expires: '2026-12-31T00:00:00Z',
        is_repeat: false,
        repeat_count: 0
      };

      const createdRx = { ...newRx, id: 10, doctor_id: 1 };
      mockAxiosInstance.post.mockResolvedValueOnce({ data: createdRx });

      const result = await api.createPrescription(newRx);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/prescriptions', newRx);
      expect(result).toEqual(createdRx);
    });
  });

  describe('Interceptors', () => {
    it('should add Authorization header to requests', async () => {
      // Re-init to attach interceptors
      api.init();
      
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce('valid_token');
      
      const config = { headers: {}, url: '/prescriptions' };
      const enhancedConfig = await requestInterceptor(config);

      expect(enhancedConfig.headers['Authorization']).toBe('Bearer valid_token');
    });

    it('should NOT add Authorization header to login request', async () => {
      api.init();
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      
      const config = { url: '/auth/login', headers: {} };
      const enhancedConfig = await requestInterceptor(config);

      expect(enhancedConfig.headers['Authorization']).toBeUndefined();
    });

    it('should handle response errors globally', async () => {
      api.init();
      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      const error = {
        response: { status: 500, data: { detail: 'Server Error' } },
        config: { url: '/prescriptions' }
      };

      await expect(errorInterceptor(error)).rejects.toEqual(error);
    });
  });

  describe('Token Refresh Flow', () => {
    it('should attempt refresh on 401 error', async () => {
      api.init();
      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      const originalRequest = { _retry: false, headers: {}, url: '/prescriptions' };
      const error = {
        config: originalRequest,
        response: { status: 401 }
      };

      // Mock refresh token available
      (AsyncStorage.getItem as jest.Mock).mockImplementation((key) => {
        if (key === 'refresh_token') return Promise.resolve('old_refresh');
        return Promise.resolve(null);
      });

      // Mock refresh success
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: { access_token: 'new_access', refresh_token: 'new_refresh' }
      });
      
      // Mock the retry call itself (the axios instance being called as a function)
      mockAxiosInstance.mockResolvedValueOnce({ data: 'retry_success' });

      const result = await errorInterceptor(error);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'old_refresh' });
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('access_token', 'new_access');
      expect(result.data).toBe('retry_success');
    });

    it('should logout if refresh fails', async () => {
      api.init();
      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      const originalRequest = { _retry: false, headers: {}, url: '/prescriptions' };
      const error = {
        config: originalRequest,
        response: { status: 401 }
      };

      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('bad_refresh');
      
      // Mock refresh failure
      mockAxiosInstance.post.mockRejectedValueOnce({ response: { status: 401 }, config: { url: '/auth/refresh' } });

      try {
        await errorInterceptor(error);
      } catch (e) {
        // Expected to throw
      }

      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('Error Handling', () => {
    it('should propagate network errors', async () => {
      const error = new Error('Network Error');
      // @ts-expect-error - Intentionally adding config property to Error
      error.config = { url: '/prescriptions' };
      mockAxiosInstance.get.mockRejectedValueOnce(error);
      await expect(api.getPrescriptions()).rejects.toThrow('Network Error');
    });

    it('should propagate 403 Forbidden', async () => {
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
        config: { url: '/prescriptions/999' }
      };
      mockAxiosInstance.get.mockRejectedValueOnce(error);
      await expect(api.getPrescription(999)).rejects.toEqual(error);
    });
  });
});
