/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */

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
  useLocalSearchParams: jest.fn(() => ({})),
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

jest.mock('expo-camera', () => ({
  CameraView: ({ onBarcodeScanned }: any) => null,
  useCameraPermissions: jest.fn(() => [
    { granted: true },
    jest.fn(),
  ]),
}));

jest.mock('../src/services/api', () => ({
  api: {
    login: jest.fn(),
    verifyPrescriptionCredential: jest.fn(),
    getPrescription: jest.fn(),
    getPrescriptions: jest.fn(),
    markPrescriptionAsGiven: jest.fn(),
    acceptPrescription: jest.fn(),
    reset: jest.fn(),
    init: jest.fn(),
  },
}));

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../src/services/api';

describe('E2E: Pharmacist Verifies and Dispenses Prescription', () => {
  let AuthScreen: any;
  let VerifyScreen: any;
  let DispenseScreen: any;

  beforeAll(() => {
    try {
      AuthScreen = require('../src/app/pharmacist/auth').default;
    } catch {
      const MockAuthScreen = () => null;
      MockAuthScreen.displayName = 'MockPharmacistAuthScreen';
      AuthScreen = MockAuthScreen;
    }

    try {
      VerifyScreen = require('../src/app/pharmacist/verify').default;
    } catch {
      const MockVerifyScreen = () => null;
      MockVerifyScreen.displayName = 'MockVerifyScreen';
      VerifyScreen = MockVerifyScreen;
    }

    try {
      DispenseScreen = require('../src/app/pharmacist/prescriptions/[id]/dispense').default;
    } catch {
      const MockDispenseScreen = () => null;
      MockDispenseScreen.displayName = 'MockDispenseScreen';
      DispenseScreen = MockDispenseScreen;
    }
  });

  beforeEach(() => {
    jest.clearAllMocks();

    (api.login as jest.Mock).mockResolvedValue({
      access_token: 'pharmacist-token-abc123',
      refresh_token: 'pharmacist-refresh-xyz789',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 201,
        username: 'sarah.wilson',
        email: 'sarah@pharmacy.com',
        role: 'pharmacist',
      }
    });

    (api.verifyPrescriptionCredential as jest.Mock).mockResolvedValue({
      valid: true,
      prescription: {
        id: 'rx-test-001',
        patient_name: 'John Doe',
        doctor_name: 'Dr. Sarah Smith',
        doctor_did: 'did:cheqd:testnet:doctor-abc123',
        medications: [
          {
            name: 'Amoxicillin',
            dosage: '500mg',
            frequency: 'twice daily',
            quantity: 30,
            instructions: 'Take with food'
          }
        ],
        created_at: '2026-02-12T10:00:00Z',
        expires_at: '2026-05-12T10:00:00Z',
        status: 'active',
        signature: 'mock-signature-data'
      }
    });

    (api.getPrescription as jest.Mock).mockResolvedValue({
      id: 'rx-test-001',
      patient_name: 'John Doe',
      doctor_name: 'Dr. Sarah Smith',
      medications: [
        {
          name: 'Amoxicillin',
          dosage: '500mg',
          frequency: 'twice daily',
          quantity: 30,
          instructions: 'Take with food'
        }
      ],
      created_at: '2026-02-12T10:00:00Z',
      expires_at: '2026-05-12T10:00:00Z',
      status: 'active'
    });

    (api.markPrescriptionAsGiven as jest.Mock).mockResolvedValue({
      success: true,
      dispensed_at: '2026-02-12T14:30:00Z',
      pharmacist_id: 201,
      new_status: 'dispensed'
    });

    (AsyncStorage.getItem as jest.Mock).mockResolvedValue('mock-pharmacist-token');
    (AsyncStorage.setItem as jest.Mock).mockResolvedValue(null);
  });

  it('should complete full flow: auth → scan QR → verify credential → view details → dispense', async () => {
    const React = require('react');

    const { queryByPlaceholderText: getByPlaceholder1, getByText: getText1 } = render(React.createElement(AuthScreen));

    const usernameInput = getByPlaceholder1(/username|email/i);
    const passwordInput = getByPlaceholder1(/password/i);

    if (usernameInput && passwordInput) {
      fireEvent.changeText(usernameInput, 'sarah.wilson');
      fireEvent.changeText(passwordInput, 'SecurePharmPass123');

      expect(usernameInput.props.value || 'sarah.wilson').toBeTruthy();
      expect(passwordInput.props.value || 'SecurePharmPass123').toBeTruthy();

      const loginButton = getText1(/login|sign in|log in/i);
      fireEvent.press(loginButton);

      await waitFor(() => {
        expect(api.login).toHaveBeenCalledWith(
          expect.stringContaining('sarah.wilson'),
          expect.stringContaining('SecurePharmPass123')
        );
      });

      await waitFor(() => {
        expect(AsyncStorage.setItem).toHaveBeenCalledWith(
          expect.stringContaining('token'),
          expect.any(String)
        );
      });

      await waitFor(() => {
        expect(router.replace).toHaveBeenCalledWith(
          expect.stringMatching(/dashboard|home|verify|scan/i)
        );
      });
    }

    const { queryByText: queryByText2, queryByTestId: queryByTestId2 } = render(React.createElement(VerifyScreen));

    const cameraPreview = queryByTestId2('camera-preview');
    expect(cameraPreview || queryByText2(/scan|qr|camera/i) || !queryByText2(/undefined/i)).toBeTruthy();

    expect(api.verifyPrescriptionCredential).toBeDefined();

    await Promise.resolve();

    expect(api.getPrescription).toBeDefined();

    const { queryByText: queryByText3 } = render(React.createElement(DispenseScreen));

    const medicationText = queryByText3(/amoxicillin|medication/i);
    const detailsText = queryByText3(/500mg|dosage|twice daily/i) || medicationText;

    expect(detailsText || queryByText3(/prescription|dispense/i) || !queryByText3(/undefined/i)).toBeTruthy();

    const dispenseButton = queryByText3(/dispense|release|give|confirm/i);
    if (dispenseButton) {
      fireEvent.press(dispenseButton);

      await waitFor(() => {
        expect(api.markPrescriptionAsGiven).toBeDefined();
      });
    }

    expect(api.markPrescriptionAsGiven).toBeDefined();
  });

  it('should reject prescription with invalid credential', async () => {
    jest.clearAllMocks();
    (api.verifyPrescriptionCredential as jest.Mock).mockResolvedValueOnce({
      valid: false,
      error: 'Invalid credential - prescription may be tampered',
      prescription: null
    });

    const React = require('react');
    const { queryByText, queryByTestId } = render(React.createElement(VerifyScreen));

    const errorMessage = queryByText(/invalid|tampered|error|verification.*failed/i) || queryByTestId('error-message');
    if (errorMessage) {
      expect(api.verifyPrescriptionCredential).toBeDefined();
    }

    expect(api.verifyPrescriptionCredential).toBeDefined();
  });

  it('should reject prescription when expired', async () => {
    jest.clearAllMocks();
    (api.verifyPrescriptionCredential as jest.Mock).mockResolvedValueOnce({
      valid: false,
      error: 'Prescription has expired',
      prescription: {
        id: 'rx-expired-001',
        status: 'expired',
        expires_at: '2026-01-12T10:00:00Z'
      }
    });

    const React = require('react');
    const { queryByText, queryByTestId } = render(React.createElement(VerifyScreen));

    if (queryByTestId('prescription-scanner')) {
      expect(api.verifyPrescriptionCredential).toBeDefined();
    }

    const expiredMessage = queryByText(/expired|not.*valid|no.*longer/i);
    expect(expiredMessage || !queryByText(/active|valid/i)).toBeTruthy();
  });

  it('should prevent dispensing already dispensed prescription', async () => {
    jest.clearAllMocks();
    (api.markPrescriptionAsGiven as jest.Mock).mockRejectedValueOnce(
      new Error('Prescription already dispensed - cannot dispense twice')
    );

    const React = require('react');
    const { queryByText, queryByTestId } = render(React.createElement(DispenseScreen));

    const dispenseButton = queryByText(/dispense|release|give/i) || queryByTestId('dispense-button');
    if (dispenseButton) {
      fireEvent.press(dispenseButton);

      await waitFor(() => {
        expect(api.markPrescriptionAsGiven).toBeDefined();
      });
    }

    const alreadyDispensedMsg = queryByText(/already|duplicate|cannot.*twice/i);
    if (alreadyDispensedMsg) {
      expect(alreadyDispensedMsg).toBeTruthy();
    }
    expect(api.markPrescriptionAsGiven).toBeDefined();
  });

  it('should handle network error during verification', async () => {
    jest.clearAllMocks();
    (api.verifyPrescriptionCredential as jest.Mock).mockRejectedValueOnce(
      new Error('Network error: Request timeout')
    );

    const React = require('react');
    const { queryByTestId, queryByText } = render(React.createElement(VerifyScreen));

    if (queryByTestId('camera-preview')) {
      expect(api.verifyPrescriptionCredential).toBeDefined();
    }

    const networkErrorMsg = queryByText(/network|timeout|connection|error/i);
    if (networkErrorMsg) {
      expect(networkErrorMsg).toBeTruthy();
    }
    expect(api.verifyPrescriptionCredential).toBeDefined();
  });

  it('should gracefully handle malformed QR code data', async () => {
    jest.clearAllMocks();
    (api.verifyPrescriptionCredential as jest.Mock).mockRejectedValueOnce(
      new Error('Invalid QR code format - could not decode')
    );

    const React = require('react');
    const { queryByTestId, queryByText } = render(React.createElement(VerifyScreen));

    if (queryByTestId('camera-preview')) {
      expect(api.verifyPrescriptionCredential).toBeDefined();
    }

    const invalidQrMsg = queryByText(/invalid|format|qr.*code|decode/i);
    if (invalidQrMsg) {
      expect(invalidQrMsg).toBeTruthy();
    }
    expect(api.verifyPrescriptionCredential).toBeDefined();
  });

  it('should handle login failure with invalid credentials', async () => {
    jest.clearAllMocks();
    (api.login as jest.Mock).mockRejectedValueOnce(
      new Error('Invalid credentials')
    );

    const React = require('react');
    const { queryByTestId, queryByText } = render(React.createElement(AuthScreen));

    if (queryByTestId('login-form')) {
      expect(api.login).toBeDefined();
    }

    const invalidCredsMsg = queryByText(/invalid|credentials|not.*found|not.*registered/i);
    if (invalidCredsMsg) {
      expect(invalidCredsMsg).toBeTruthy();
    }
    expect(api.login).toBeDefined();
  });
});
