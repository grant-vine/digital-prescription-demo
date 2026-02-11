import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// --- Types ---

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
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

export interface Prescription {
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

export interface PrescriptionCreate {
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

export interface PaginatedResponse {
  items: Prescription[];
  total: number;
  page: number;
  page_size: number;
}

export interface PatientSearchResult {
  id: number;
  name: string;
  medical_record: string;
  did?: string;
  date_of_birth?: string;
}

export interface PatientSearchResponse {
  items: PatientSearchResult[];
  total: number;
}

export interface MedicationSearchResult {
  id: number;
  name: string;
  code: string;
  generic_name: string;
  strength: string;
  form: string;
}

export interface MedicationSearchResponse {
  items: MedicationSearchResult[];
  total: number;
}

// --- Axios Instance ---

const API_URL = 'http://localhost:8000'; // In real app, this should be env var

let _axiosInstance: AxiosInstance | null = null;

const getClient = (): AxiosInstance => {
  if (_axiosInstance) return _axiosInstance;

  _axiosInstance = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // --- Interceptors ---

  // Request Interceptor: Add Auth Token
  _axiosInstance.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      // Skip auth header for login/refresh endpoints
      if (config.url?.includes('/auth/login') || config.url?.includes('/auth/refresh')) {
        return config;
      }

      try {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Error retrieving token', error);
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response Interceptor: Handle Token Refresh
  interface RetryQueueItem {
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }

  let isRefreshing = false;
  let failedQueue: RetryQueueItem[] = [];

  const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
      if (error) {
        prom.reject(error);
      } else {
        prom.resolve(token);
      }
    });

    failedQueue = [];
  };

  _axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // Skip refresh logic for login endpoint
      if (originalRequest.url?.includes('/auth/login')) {
        return Promise.reject(error);
      }

      // If 401 Unauthorized and we haven't retried yet
      if (error.response?.status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          // If already refreshing, add to queue
          return new Promise(function (resolve, reject) {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              if (_axiosInstance) {
                 originalRequest.headers.Authorization = `Bearer ${token}`;
                 return _axiosInstance(originalRequest);
              }
              return Promise.reject(new Error('Axios instance lost'));
            })
            .catch((err) => {
              return Promise.reject(err);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const refreshToken = await AsyncStorage.getItem('refresh_token');

          if (!refreshToken) {
            throw new Error('No refresh token available');
          }

          if (!_axiosInstance) throw new Error('Axios instance lost');

          const response = await _axiosInstance.post('/auth/refresh', {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;

          await AsyncStorage.setItem('access_token', access_token);
          await AsyncStorage.setItem('refresh_token', newRefreshToken);

          // Process queue with new token
          processQueue(null, access_token);

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return _axiosInstance(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          // Refresh failed - logout user
          await AsyncStorage.removeItem('access_token');
          await AsyncStorage.removeItem('refresh_token');
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      return Promise.reject(error);
    }
  );

  return _axiosInstance;
};

// --- API Methods ---

export const api = {
  // Expose init for testing purposes or early initialization
  init: () => getClient(),
  
  // Expose reset for testing
  reset: () => { _axiosInstance = null; },

  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await getClient().post('/auth/login', { username, password });
    const { access_token, refresh_token } = response.data;
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('refresh_token', refresh_token);
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await getClient().post('/auth/logout');
    } finally {
      // Always clear tokens even if server call fails
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('refresh_token');
    }
  },

  async getPrescriptions(page = 1, page_size = 10): Promise<PaginatedResponse> {
    const response = await getClient().get('/prescriptions', {
      params: { page, page_size },
    });
    return response.data;
  },

  async getPrescription(id: number): Promise<Prescription> {
    const response = await getClient().get(`/prescriptions/${id}`);
    return response.data;
  },

  async createPrescription(data: PrescriptionCreate): Promise<Prescription> {
    const response = await getClient().post('/prescriptions', data);
    return response.data;
  },

  async searchPatients(query: string | { query: string }): Promise<PatientSearchResponse> {
    const q = typeof query === 'string' ? query : query.query;
    const response = await getClient().get('/patients/search', {
      params: { q },
    });
    return response.data;
  },

  async getPatient(id: number): Promise<PatientSearchResult> {
    const response = await getClient().get(`/patients/${id}`);
    return response.data;
  },

  async searchMedications(query: string | { query: string }): Promise<MedicationSearchResponse> {
    const q = typeof query === 'string' ? query : query.query;
    const response = await getClient().get('/medications/search', {
      params: { q },
    });
    return response.data;
  },
};
