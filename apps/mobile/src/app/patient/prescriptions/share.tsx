import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import QRCode from 'react-native-qrcode-svg';
import { api, VerifiablePresentation } from '../../../services/api';
import { PatientTheme } from '../../../components/theme/PatientTheme';

interface Medication {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  quantity: string;
  instructions: string;
}

interface Prescription {
  id: string | number;
  patient_name: string;
  patient_id: string | number;
  doctor_name: string;
  doctor_did: string;
  medications: Medication[];
  created_at: string;
  expires_at?: string;
  date_expires?: string;
  status: 'active' | 'expired' | 'used';
  signature?: string;
  digital_signature?: string;
  verified: boolean;
}

const PHARMACIES = [
  { id: 'pharmacy-001', name: 'City Pharmacy' },
  { id: 'pharmacy-002', name: 'Health Plus Pharmacy' },
  { id: 'pharmacy-003', name: 'Care Pharmacy' },
];

const ThemedText = ({ children, style, testID, ...props }: any) => (
  <Text style={[{ color: PatientTheme.colors.text }, style]} testID={testID} {...props}>
    {children}
  </Text>
);

const ThemedButton = ({ title, onPress, disabled, testID }: any) => (
  <TouchableOpacity
    onPress={onPress}
    disabled={disabled}
    testID={testID}
    style={[styles.button, disabled && styles.buttonDisabled]}
  >
    <Text style={styles.buttonText}>{title}</Text>
  </TouchableOpacity>
);

export default function SharePrescriptionScreen() {
  const { id } = useLocalSearchParams();
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [presentation, setPresentation] = useState<VerifiablePresentation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPharmacy, setSelectedPharmacy] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(900);

  // Load prescription preview
  const loadPrescription = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const result = await api.getPrescription(id as string);
      setPrescription(result as Prescription);
    } catch (err: any) {
      setError(err.message || 'Failed to load prescription');
      setPrescription(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const fetchData = async () => {
      await Promise.resolve();
      await loadPrescription();
    };
    fetchData();
  }, [loadPrescription]);

  // Countdown timer
  useEffect(() => {
    if (presentation && timeRemaining > 0) {
      const interval = setInterval(() => {
        setTimeRemaining(prev => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [presentation, timeRemaining]);

  const handleGenerateQR = async () => {
    try {
      setLoading(true);
      setError('');
      const result = await api.generatePresentation(id as string);
      if (result.presentation) {
        setPresentation(result.presentation);
        setTimeRemaining(900);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  const handlePharmacySelect = async (pharmacyId: string) => {
    setSelectedPharmacy(pharmacyId);
    try {
      await api.selectPharmacy(pharmacyId);
    } catch (err) {
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleRetry = () => {
    setError('');
    handleGenerateQR();
  };

  // Loading state
  if (loading && !prescription && !presentation) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator
          size="large"
          color={PatientTheme.colors.primary}
          testID="loading-indicator"
        />
        <ThemedText style={styles.loadingText}>Loading prescription...</ThemedText>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={styles.centerContainer}>
        <ThemedText testID="error-message" style={styles.errorText}>
          {error}
        </ThemedText>
        <ThemedButton title="Retry" onPress={handleRetry} testID="retry-button" />
      </View>
    );
  }

  // QR Display Mode - Show after generation
  if (presentation) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
      >
        {/* Confirmation message */}
        <ThemedText style={styles.confirmationTitle} testID="confirmation-message">
          Ready to Share
        </ThemedText>

        <ThemedText style={styles.confirmationText}>
          Your prescription is ready to share with the pharmacist. Ask them to scan the QR code below.
        </ThemedText>

        {/* QR Code Section */}
        <View style={styles.qrSection}>
          <View style={styles.qrContainer} testID="qr-code">
            <QRCode
              value={JSON.stringify(presentation)}
              size={300}
              backgroundColor="#FFFFFF"
              color="#000000"
            />
          </View>
        </View>

        {/* Countdown Timer */}
        <View style={styles.timerSection}>
          <ThemedText style={styles.timerLabel} testID="timer">
            Valid for: {formatTime(timeRemaining)}
          </ThemedText>
          <ThemedText style={styles.timerSubtext}>
            QR code expires in {Math.floor(timeRemaining / 60)} minute{Math.floor(timeRemaining / 60) !== 1 ? 's' : ''}
          </ThemedText>
        </View>

        {/* Instructions */}
        <View style={styles.instructionsSection}>
          <ThemedText style={styles.instructionsTitle} testID="scan-instructions">
            Instructions for pharmacist:
          </ThemedText>
          <ThemedText style={styles.instructionsText}>
            1. Ask the pharmacist to scan this QR code{'\n'}
            2. They will verify the prescription authenticity{'\n'}
            3. Once verified, they can dispense your medications
          </ThemedText>
        </View>

        {/* Regenerate button when expired */}
        {timeRemaining === 0 && (
          <ThemedButton
            title="Generate New QR Code"
            onPress={handleGenerateQR}
            testID="regenerate-button"
          />
        )}
      </ScrollView>
    );
  }

  // Preview Mode - Show prescription details with share button
  if (!prescription) {
    return (
      <View style={styles.centerContainer}>
        <ThemedText style={styles.emptyText}>Prescription not found</ThemedText>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      {/* Prescription Preview Section */}
      <View style={styles.previewSection}>
        <ThemedText style={styles.sectionTitle}>Prescription Preview</ThemedText>

        <View style={styles.previewCard}>
          <ThemedText style={styles.patientName}>
            {prescription.patient_name}
          </ThemedText>

          <ThemedText style={[styles.medicationLabel, { marginTop: PatientTheme.spacing.md }]}>
            Medications:
          </ThemedText>
          <ThemedText style={styles.medicationsList}>
            {prescription.medications.map(m => m.name).join(', ')}
          </ThemedText>

          <ThemedText style={[styles.medicationLabel, { marginTop: PatientTheme.spacing.md }]}>
            Prescribed by:
          </ThemedText>
          <ThemedText style={styles.doctorName}>
            {prescription.doctor_name}
          </ThemedText>
        </View>
      </View>

      {/* Pharmacy Selection Section */}
      <View style={styles.pharmacySection} testID="pharmacy-select">
        <ThemedText style={styles.sectionTitle}>
          Select Location
        </ThemedText>

        <View style={styles.pharmacyList}>
          {PHARMACIES.map(pharmacy => (
            <TouchableOpacity
              key={pharmacy.id}
              style={[
                styles.pharmacyButton,
                selectedPharmacy === pharmacy.id && styles.pharmacyButtonSelected,
              ]}
              onPress={() => handlePharmacySelect(pharmacy.id)}
              testID="pharmacy-option"
            >
              <ThemedText style={styles.pharmacyButtonText}>
                {pharmacy.id.includes('001') ? 'Option 1' : pharmacy.id.includes('002') ? 'Option 2' : 'Option 3'}
              </ThemedText>
            </TouchableOpacity>
          ))}
        </View>

        {selectedPharmacy && (
          <ThemedText style={styles.selectedPharmacyText}>
            {PHARMACIES.find(p => p.id === selectedPharmacy)?.name} selected
          </ThemedText>
        )}
      </View>

      {/* Share Button */}
      <View style={styles.actionSection}>
        <ThemedButton
          title="Generate QR Code"
          onPress={handleGenerateQR}
          testID="share-button"
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: PatientTheme.colors.background,
  },
  content: {
    padding: PatientTheme.spacing.lg,
    paddingBottom: PatientTheme.spacing.xl,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: PatientTheme.colors.background,
    padding: PatientTheme.spacing.lg,
  },
  previewSection: {
    marginBottom: PatientTheme.spacing.lg,
  },
  pharmacySection: {
    marginBottom: PatientTheme.spacing.lg,
  },
  qrSection: {
    alignItems: 'center',
    marginVertical: PatientTheme.spacing.lg,
  },
  qrContainer: {
    padding: PatientTheme.spacing.md,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  sectionTitle: {
    ...PatientTheme.typography.heading,
    color: PatientTheme.colors.primary,
    marginBottom: PatientTheme.spacing.md,
  },
  previewCard: {
    backgroundColor: PatientTheme.colors.surface,
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  patientName: {
    fontSize: 16,
    fontWeight: '600',
    color: PatientTheme.colors.text,
  },
  medicationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: PatientTheme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  medicationsList: {
    fontSize: 14,
    fontWeight: '500',
    color: PatientTheme.colors.text,
    marginTop: 4,
  },
  doctorName: {
    fontSize: 14,
    fontWeight: '500',
    color: PatientTheme.colors.text,
    marginTop: 4,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    overflow: 'hidden',
    marginBottom: PatientTheme.spacing.md,
  },
  picker: {
    color: PatientTheme.colors.text,
  },
  pharmacyList: {
    marginBottom: PatientTheme.spacing.md,
    gap: PatientTheme.spacing.sm,
  },
  pharmacyButton: {
    paddingVertical: PatientTheme.spacing.md,
    paddingHorizontal: PatientTheme.spacing.md,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 6,
    backgroundColor: '#FFFFFF',
  },
  pharmacyButtonSelected: {
    backgroundColor: PatientTheme.colors.primary,
    borderColor: PatientTheme.colors.primary,
  },
  pharmacyButtonText: {
    color: PatientTheme.colors.text,
    fontSize: 14,
    fontWeight: '500',
  },
  selectedPharmacyText: {
    fontSize: 12,
    fontStyle: 'italic',
    color: PatientTheme.colors.textSecondary,
    marginTop: PatientTheme.spacing.sm,
  },
  timerSection: {
    alignItems: 'center',
    marginVertical: PatientTheme.spacing.lg,
    padding: PatientTheme.spacing.md,
    backgroundColor: '#F0F9FF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: PatientTheme.colors.primary,
  },
  timerLabel: {
    fontSize: 20,
    fontWeight: '700',
    color: PatientTheme.colors.primary,
    fontFamily: 'Courier New',
  },
  timerSubtext: {
    fontSize: 12,
    color: PatientTheme.colors.textSecondary,
    marginTop: PatientTheme.spacing.sm,
  },
  instructionsSection: {
    marginVertical: PatientTheme.spacing.lg,
    padding: PatientTheme.spacing.md,
    backgroundColor: PatientTheme.colors.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  instructionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: PatientTheme.colors.primary,
    marginBottom: PatientTheme.spacing.sm,
  },
  instructionsText: {
    fontSize: 13,
    lineHeight: 20,
    color: PatientTheme.colors.text,
  },
  confirmationTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: PatientTheme.colors.primary,
    marginBottom: PatientTheme.spacing.md,
  },
  confirmationText: {
    fontSize: 14,
    color: PatientTheme.colors.text,
    marginBottom: PatientTheme.spacing.lg,
    lineHeight: 20,
  },
  actionSection: {
    marginTop: PatientTheme.spacing.lg,
    paddingBottom: PatientTheme.spacing.lg,
  },
  button: {
    backgroundColor: PatientTheme.colors.primary,
    paddingVertical: PatientTheme.spacing.md,
    paddingHorizontal: PatientTheme.spacing.lg,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#94A3B8',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingText: {
    marginTop: PatientTheme.spacing.md,
    fontSize: 16,
  },
  errorText: {
    color: PatientTheme.colors.error,
    marginBottom: PatientTheme.spacing.lg,
    textAlign: 'center',
    fontSize: 16,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
