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

export interface ExtendedPrescription extends Prescription {
  patient_name?: string;
  doctor_name?: string;
  doctor_did?: string;
  medications?: Array<{
    name: string;
    dosage: string;
    frequency: string;
    duration: string;
    quantity: string;
    instructions: string;
  }>;
  expires_at?: string;
  status?: 'active' | 'expired' | 'used';
  signature?: string;
  verified?: boolean;
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

export interface PrescriptionDraft {
  id: string;
  patient_name: string;
  patient_id: number;
  medications: Array<{
    name: string;
    dosage: string;
    instructions: string;
  }>;
  repeat_count: number;
  repeat_interval: string;
  created_at: string;
}

export interface SignPrescriptionResponse {
  success: boolean;
  prescription_id: string;
  signature: string;
  signed_at?: string;
}

export interface VerifiablePresentation {
  '@context': string[];
  type: string;
  id?: string;
  created?: string;
  expiresAt?: string;
  holder?: string;
  verifiableCredential?: any[];
  proof?: any;
}

export interface PresentationResponse {
  presentation: VerifiablePresentation;
  qrData?: string;
}

export interface DispensingAction {
  prescriptionId: string | string[];
  action: string;
  items?: string[];
  timestamp: string;
}

// --- Axios Instance ---

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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
      if (config.url?.includes('/api/v1/auth/login') || config.url?.includes('/api/v1/auth/refresh')) {
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
      if (originalRequest.url?.includes('/api/v1/auth/login')) {
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

  async getPrescription(id: number | string): Promise<ExtendedPrescription> {
    const response = await getClient().get(`/prescriptions/${id}`);
    return response.data;
  },

  async createPrescription(data: PrescriptionCreate): Promise<Prescription> {
    const response = await getClient().post('/prescriptions', data);
    return response.data;
  },

  async searchPatients(_query: string | { query: string }): Promise<PatientSearchResponse> {
    console.warn('Patient search using mock data');
    return {
      items: [
        { id: 1, name: 'John Smith', medical_record: 'MR001', did: 'did:web:patient1', date_of_birth: '1985-03-15' },
        { id: 2, name: 'Jane Doe', medical_record: 'MR002', did: 'did:web:patient2', date_of_birth: '1990-07-22' },
      ],
      total: 2
    };
  },

  async getPatient(id: number): Promise<PatientSearchResult> {
    console.warn('Get patient using mock data');
    return {
      id,
      name: 'John Smith',
      medical_record: 'MR001',
      did: 'did:web:patient1',
      date_of_birth: '1985-03-15'
    };
  },

  async searchMedications(_query: string | { query: string }): Promise<MedicationSearchResponse> {
    console.warn('Medication search using mock data');
    return {
      items: [
        { id: 1, name: 'Amoxicillin', code: 'AMOX500', generic_name: 'Amoxicillin', strength: '500mg', form: 'Capsule' },
        { id: 2, name: 'Ibuprofen', code: 'IBU200', generic_name: 'Ibuprofen', strength: '200mg', form: 'Tablet' },
      ],
      total: 2
    };
  },

  async getPrescriptionDraft(prescriptionId: string): Promise<PrescriptionDraft> {
    console.warn('Get prescription draft using mock data');
    return {
      id: prescriptionId,
      patient_name: 'John Smith',
      patient_id: 2,
      medications: [
        { name: 'Amoxicillin', dosage: '500mg', instructions: 'Take 3 times daily' }
      ],
      repeat_count: 0,
      repeat_interval: '30 days',
      created_at: new Date().toISOString()
    };
  },

  async signPrescription(prescriptionId: string): Promise<SignPrescriptionResponse> {
    const response = await getClient().post(`/prescriptions/${prescriptionId}/sign`, {});
    return response.data;
  },

  async createWallet(): Promise<{ wallet_id: string; did: string; created_at: string }> {
    const response = await getClient().post('/wallet/setup');
    return response.data;
  },

  async setupPatientDID(_walletId: string): Promise<{ did: string; did_document: any }> {
    console.warn('Setup patient DID using mock data');
    return {
      did: 'did:web:example.com:patient:123',
      did_document: { id: 'did:web:example.com:patient:123' }
    };
  },

  async authenticatePatient(username: string, password: string): Promise<{ token: string; patient: any }> {
    const response = await getClient().post('/auth/login', { username, password });
    const { access_token, user } = response.data;
    return { token: access_token, patient: user };
  },

  async verifyCredential(credential: any): Promise<any> {
    const response = await getClient().post('/verify/prescription', credential);
    return response.data;
  },

  async acceptPrescription(prescriptionId: string): Promise<any> {
    console.warn('Accept prescription using mock data');
    return { success: true, prescriptionId };
  },

   async markPrescriptionAsGiven(prescriptionId: string): Promise<any> {
     console.warn('Mark prescription as given using mock data');
     return { success: true, prescriptionId, status: 'dispensed' };
   },

   async verifyPrescriptionCredential(qrData: any): Promise<any> {
     const response = await getClient().post('/verify/prescription', qrData);
     return response.data;
   },

   async rejectPrescription(prescriptionId: string, reason: string): Promise<any> {
     console.warn('Reject prescription using mock data');
     return { success: true, prescriptionId, reason, status: 'rejected' };
   },

   async getPrescriptionByCode(code: string): Promise<any> {
     console.warn('Get prescription by code using mock data');
     return {
       id: 1,
       code,
       medication_name: 'Amoxicillin',
       status: 'active'
     };
   },

  async authenticatePharmacist(username: string, password: string): Promise<{ token: string; pharmacist: { id: string; name: string } }> {
    const response = await getClient().post('/auth/login', { username, password });
    const { access_token, user } = response.data;
    return { 
      token: access_token, 
      pharmacist: { 
        id: user.id.toString(), 
        name: user.username 
      } 
    };
  },

  async validateSAPC(sapcNumber: string): Promise<{ valid: boolean; registration: any }> {
    console.warn('Validate SAPC using mock data');
    return {
      valid: true,
      registration: {
        sapc_number: sapcNumber,
        name: 'Demo Pharmacist',
        status: 'active'
      }
    };
  },

  async setupPharmacy(_data: { pharmacy_name: string; sapc_number: string }): Promise<{ pharmacy_id: string; status: string }> {
    console.warn('Setup pharmacy using mock data');
    return {
      pharmacy_id: 'pharm-001',
      status: 'active'
    };
  },

  async createPharmacistDID(_pharmacistId: string): Promise<{ did: string; did_document: any }> {
    console.warn('Create pharmacist DID using mock data');
    return {
      did: 'did:web:example.com:pharmacist:123',
      did_document: { id: 'did:web:example.com:pharmacist:123' }
    };
  },

  async verifyPrescription(qrData: any): Promise<{ valid: boolean; signature_valid: boolean; issuer: any; trust_registry_status: string; revocation_status: string; error?: string }> {
    const response = await getClient().post('/verify/prescription', qrData);
    return response.data;
  },

  async checkTrustRegistry(issuerDid: string): Promise<{ trusted: boolean; registry: string }> {
    const response = await getClient().post('/verify/trust-registry', { issuer_did: issuerDid });
    return response.data;
  },

  async checkRevocationStatus(prescriptionId: string): Promise<{ revoked: boolean; status: string }> {
    const response = await getClient().get(`/prescriptions/${prescriptionId}/revocation-status`);
    return response.data;
  },

  async verifyPresentation(code: string): Promise<{ valid: boolean; issuer: any; trust_registry_status: string; revocation_status: string; error?: string }> {
    const response = await getClient().post('/verify/presentation', { code });
    return response.data;
  },

  async generatePresentation(prescriptionId: string | string[]): Promise<PresentationResponse> {
    const response = await getClient().post(`/prescriptions/${prescriptionId}/presentation`);
    return response.data;
  },

  async selectPharmacy(pharmacyId: string): Promise<{ success: boolean }> {
    const response = await getClient().post('/pharmacies/select', { pharmacy_id: pharmacyId });
    return response.data;
  },

  async getVerifiedPrescription(prescriptionId: string | string[]): Promise<any> {
    const response = await getClient().get(`/prescriptions/${prescriptionId}/verified`);
    return response.data;
  },

  async dispenseMedication(prescriptionId: string | string[]): Promise<{ success: boolean }> {
    const response = await getClient().post(`/prescriptions/${prescriptionId}/dispense`);
    return response.data;
  },

  async partialDispense(prescriptionId: string | string[], medicationNames: string[]): Promise<{ success: boolean }> {
    const response = await getClient().post(`/prescriptions/${prescriptionId}/partial-dispense`, {
      medications: medicationNames,
    });
    return response.data;
  },

  async logDispensingAction(action: DispensingAction): Promise<{ success: boolean }> {
    const response = await getClient().post('/dispensing/log', action);
    return response.data;
  },
};
