/**
 * API Client Tests
 *
 * TDD test suite for backend API client wrapper.
 * All tests are designed to FAIL until api service is implemented in TASK-030.
 *
 * Test Categories:
 * 1. Authentication (Login, Refresh, Logout)
 * 2. Prescription Management (List, Get, Create)
 * 3. Error Handling (Network, 401, 403, 404, 500)
 * 4. Interceptors (Request injection, Response handling)
 * 5. Token Management (Storage, Refresh flow)
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */

// Types matching Backend Pydantic Schemas
interface LoginRequest {
  username: string; // Backend uses username, not email
  password: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username: string;
    email: string;
    role: string;
  };
}

interface Prescription {
  id: number;
  doctor_id: number;
  patient_id: number;
  medication_name: string;
  medication_code?: string;
  dosage: string;
  quantity: number;
  instructions?: string;
  date_issued: string;
  date_expires: string;
  is_repeat: boolean;
  repeat_count: number;
  digital_signature?: string;
  created_at: string;
  updated_at: string;
}

interface PrescriptionCreate {
  patient_id: number;
  medication_name: string;
  medication_code: string;
  dosage: string;
  quantity: number;
  instructions: string;
  date_expires: string;
  is_repeat: boolean;
  repeat_count: number;
}

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  defaults: { headers: { common: {} } },
}), { virtual: true });
// @ts-expect-error
import axios from 'axios';
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>;

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}), { virtual: true });
// @ts-expect-error
import AsyncStorage from '@react-native-async-storage/async-storage';

// Dynamic require for API module (not yet implemented)
let api: any;
try {
  api = require('./api');
} catch (e) {
  api = null;
}

describe('API Client', () => {
  // Mock axios instance
  const mockAxiosInstance = {
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    request: jest.fn(),
    defaults: { headers: { common: {} } },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // Setup axios create mock
    mockedAxios.create.mockReturnValue(mockAxiosInstance as any);
  });

  describe('Initialization', () => {
    it('should be defined', () => {
      // EXPECTED FAILURE: api module does not exist
      expect(api).toBeTruthy();
    });

    it('should create axios instance with base URL', () => {
      if (!api) { expect(api).toBeTruthy(); return; } // Skip if api not loaded (fail via previous test)
      
      // Expected behavior: api.init() or module load creates instance
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.stringContaining('http'),
          timeout: expect.any(Number),
        })
      );
    });
  });

  describe('Authentication', () => {
    it('should login successfully and store tokens', async () => {
      // EXPECTED FAILURE: api.login not implemented
      if (!api) {
         expect(api).toBeTruthy(); 
         return;
      }

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
      if (!api) { expect(api).toBeTruthy(); return; }

      mockAxiosInstance.post.mockRejectedValueOnce({
        response: { status: 401, data: { detail: 'Invalid credentials' } }
      });

      await expect(api.login('wrong', 'pass')).rejects.toThrow();
    });

    it('should logout and clear tokens', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      mockAxiosInstance.post.mockResolvedValueOnce({ data: { message: 'Logged out' } });

      await api.logout();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/logout');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('Prescriptions', () => {
    it('should list prescriptions', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

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
      if (!api) { expect(api).toBeTruthy(); return; }

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
      if (!api) { expect(api).toBeTruthy(); return; }

      mockAxiosInstance.get.mockRejectedValueOnce({
        response: { status: 404, data: { detail: 'Not found' } }
      });

      await expect(api.getPrescription(999)).rejects.toThrow();
    });

    it('should create prescription', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

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
      if (!api) { expect(api).toBeTruthy(); return; }

      // Get the request interceptor callback
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce('valid_token');
      
      const config = { headers: {} };
      const enhancedConfig = await requestInterceptor(config);

      expect(enhancedConfig.headers['Authorization']).toBe('Bearer valid_token');
    });

    it('should NOT add Authorization header to login request', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      
      const config = { url: '/auth/login', headers: {} };
      const enhancedConfig = await requestInterceptor(config);

      expect(enhancedConfig.headers['Authorization']).toBeUndefined();
    });

    it('should handle response errors globally', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      // Get the response interceptor error callback
      // Usually [0] is success handler, [1] is error handler
      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      const error = {
        response: { status: 500, data: { detail: 'Server Error' } }
      };

      await expect(errorInterceptor(error)).rejects.toEqual(error);
    });
  });

  describe('Token Refresh Flow', () => {
    it('should attempt refresh on 401 error', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      // Setup: 401 error on original request
      const originalRequest = { _retry: false, headers: {} };
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
      
      // Mock retry success
      mockAxiosInstance.request = jest.fn().mockResolvedValue({ data: 'retry_success' });

      const result = await errorInterceptor(error);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: 'old_refresh' });
      expect(AsyncStorage.setItem).toHaveBeenCalledWith('access_token', 'new_access');
      expect(result.data).toBe('retry_success');
    });

    it('should logout if refresh fails', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      const originalRequest = { _retry: false, headers: {} };
      const error = {
        config: originalRequest,
        response: { status: 401 }
      };

      (AsyncStorage.getItem as jest.Mock).mockResolvedValue('bad_refresh');
      
      // Mock refresh failure
      mockAxiosInstance.post.mockRejectedValueOnce({ response: { status: 401 } });

      // Mock logout (spy on module method if possible, or check side effects)
      // Since api is local var, we check side effects (clearing storage)
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
      if (!api) { expect(api).toBeTruthy(); return; }

      mockAxiosInstance.get.mockRejectedValueOnce(new Error('Network Error'));
      await expect(api.getPrescriptions()).rejects.toThrow('Network Error');
    });

    it('should propagate 403 Forbidden', async () => {
      if (!api) { expect(api).toBeTruthy(); return; }

      mockAxiosInstance.get.mockRejectedValueOnce({
        response: { status: 403, data: { detail: 'Forbidden' } }
      });
      await expect(api.getPrescription(999)).rejects.toEqual(expect.objectContaining({
        response: { status: 403 }
      }));
    });
  });
});
