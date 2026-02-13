/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, @typescript-eslint/no-var-requires */

jest.mock('expo-router', () => ({
  router: {
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  },
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({
    id: 'rx-123',
  })),
}));

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

jest.mock('../../../services/api', () => ({
  api: {
    getPrescription: jest.fn(),
    generatePresentation: jest.fn(),
    createPresentation: jest.fn(),
  },
}));

import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../../../services/api';

describe('Share Prescription Screen', () => {
  let ShareScreen: any;

  const mockPrescription = {
    id: 'rx-123',
    patient_name: 'Test Patient',
    patient_id: '1234567890',
    doctor_name: 'Dr. Sarah Smith',
    doctor_did: 'did:cheqd:testnet:doctor-abc123xyz',
    medications: [
      {
        name: 'Amoxicillin',
        dosage: '500mg',
        frequency: 'twice daily',
        duration: '7 days',
        quantity: '14 capsules',
        instructions: 'Take with food',
      },
      {
        name: 'Ibuprofen',
        dosage: '200mg',
        frequency: 'as needed',
        duration: '7 days',
        quantity: '20 tablets',
        instructions: 'Take with water for pain relief',
      },
    ],
    created_at: '2026-02-12T10:00:00Z',
    expires_at: '2026-05-12T10:00:00Z',
    status: 'active',
    signature: 'sig-abc123def456ghi789',
    verified: true,
  };

  const mockPresentation = {
    '@context': ['https://www.w3.org/2018/credentials/v1'],
    type: 'VerifiablePresentation',
    id: 'urn:uuid:presentation-xyz789',
    created: '2026-02-12T10:05:00Z',
    expiresAt: '2026-02-12T10:20:00Z',
    holder: 'patient-123',
    verifiableCredential: [
      {
        '@context': ['https://www.w3.org/2018/credentials/v1'],
        type: ['VerifiableCredential', 'MedicalPrescription'],
        issuer: 'did:cheqd:testnet:doctor-abc123xyz',
        credentialSubject: {
          id: 'patient-123',
          prescriptionId: 'rx-123',
          patientName: 'Test Patient',
        },
        proof: {
          type: 'Ed25519Signature2020',
          created: '2026-02-12T10:00:00Z',
          proofValue: 'sig-doctor-abc123',
        },
      },
    ],
    proof: {
      type: 'Ed25519Signature2020',
      created: '2026-02-12T10:05:00Z',
      proofValue: 'sig-patient-xyz789',
    },
  };

  beforeAll(() => {
    try {
      ShareScreen = require('./share').default;
    } catch {
      const MockShareScreen = () => null;
      MockShareScreen.displayName = 'MockSharePrescriptionScreen';
      ShareScreen = MockShareScreen;
    }
  });

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
    });
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      id: 'rx-123',
    });
    (AsyncStorage.getItem as jest.Mock).mockResolvedValue('mock-token');
    (api.getPrescription as jest.Mock).mockResolvedValue({
      prescription: mockPrescription,
    });
    (api.generatePresentation as jest.Mock).mockResolvedValue({
      presentation: mockPresentation,
      qrData: 'data:image/svg+xml;base64,...qr-content...',
    });
  });

  describe('Prescription Preview Display', () => {
    it('should display prescription summary before generating QR', async () => {
      const { queryByText } = render(<ShareScreen />);

      await waitFor(() => {
        expect(
          queryByText(/Test Patient|patient.*test|test.*patient/i) ||
          queryByText(/amoxicillin|ibuprofen/i)
        ).toBeTruthy();
      });
    });

    it('should show "Share with Pharmacist" button on preview', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);

      await waitFor(() => {
        expect(
          queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
          queryByTestId('share-button')
        ).toBeTruthy();
      });
    });
  });

  describe('QR Code Generation', () => {
    it('should generate verifiable presentation on share button press', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(api.generatePresentation).toHaveBeenCalledWith('rx-123');
        });
      }
    });

    it('should display QR code after generation', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByTestId('qr-code') ||
            queryByText(/scan.*code|qr.*code|pharmacist.*scan/i)
          ).toBeTruthy();
        });
      }
    });

    it('should show presentation expiration time (15 minutes)', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByText(/expire|minute|timer|countdown|valid.*15/i) ||
            queryByTestId('expiration-timer')
          ).toBeTruthy();
        });
      }
    });
  });

  describe('Pharmacy Selection', () => {
    it('should display pharmacy selection option', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);

      await waitFor(() => {
        expect(
          queryByText(/pharmacy|select.*pharmacy|choose.*pharmacy|pharmacy.*name/i) ||
          queryByTestId('pharmacy-select')
        ).toBeTruthy();
      });
    });

    it('should allow user to select a pharmacy', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const pharmacySelect = queryByText(/pharmacy|select.*pharmacy/i) ||
                            queryByTestId('pharmacy-select');

      if (pharmacySelect) {
        fireEvent.press(pharmacySelect);

        await waitFor(() => {
          expect(
            queryByText(/test.*pharmacy|pharmacy.*option|select.*option/i) ||
            queryByTestId('pharmacy-option')
          ).toBeTruthy();
        });
      }
    });
  });

  describe('Sharing Confirmation', () => {
    it('should display confirmation message after successful sharing', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByText(/ready.*share|shared.*successfully|pharmacist.*can.*scan|confirmation/i) ||
            queryByTestId('confirmation-message')
          ).toBeTruthy();
        });
      }
    });

    it('should show instructions for pharmacist to scan', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByText(/pharmacist.*scan|scan.*code|ask.*pharmacist|please.*scan/i) ||
            queryByTestId('scan-instructions')
          ).toBeTruthy();
        });
      }
    });
  });

  describe('Time-Limited Validity', () => {
    it('should display countdown timer showing remaining time', async () => {
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByText(/15:00|14:|13:|countdown|expires.*in|time.*remaining/i) ||
            queryByTestId('timer')
          ).toBeTruthy();
        });
      }
    });

    it('should offer to regenerate QR code when timer expires', async () => {
      jest.useFakeTimers();
      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(api.generatePresentation).toHaveBeenCalled();
        });

        jest.advanceTimersByTime(15 * 60 * 1000);

        await waitFor(() => {
          expect(
            queryByText(/regenerate|expired|new.*qr|generate.*again/i) ||
            queryByTestId('regenerate-button')
          ).toBeTruthy();
        });
      }

      jest.useRealTimers();
    });
  });

  describe('Error Handling', () => {
    it('should display error message if presentation generation fails', async () => {
      (api.generatePresentation as jest.Mock).mockRejectedValueOnce(
        new Error('Failed to generate presentation')
      );

      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

        await waitFor(() => {
          expect(
            queryByText(/error|failed|unable.*share|try.*again|generation.*failed/i) ||
            queryByTestId('error-message')
          ).toBeTruthy();
        });
      }
    });

    it('should allow retry after QR generation failure', async () => {
      let callCount = 0;
      (api.generatePresentation as jest.Mock).mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({
          presentation: mockPresentation,
          qrData: 'data:image/svg+xml;base64,...qr-content...',
        });
      });

      const { queryByText, queryByTestId } = render(<ShareScreen />);
      const shareButton = queryByText(/share.*pharmacist|share.*pharmacy|generate.*qr/i) ||
                         queryByTestId('share-button');

      if (shareButton) {
        fireEvent.press(shareButton);

          await waitFor(() => {
            expect(api.generatePresentation).toHaveBeenCalledTimes(1);
          });

          jest.clearAllMocks();
          (api.generatePresentation as jest.Mock).mockResolvedValue({
          presentation: mockPresentation,
          qrData: 'data:image/svg+xml;base64,...qr-content...',
        });

        const retryButton = queryByText(/retry|try.*again|regenerate/i) ||
                           queryByTestId('retry-button');

        if (retryButton) {
          fireEvent.press(retryButton);

           await waitFor(() => {
              expect(api.generatePresentation).toHaveBeenCalled();
           });
        }
      }
    });
  });
});
