import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { api } from '../../../services/api';
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
  id: string;
  patient_name: string;
  patient_id: string;
  doctor_name: string;
  doctor_did: string;
  medications: Medication[];
  created_at: string;
  expires_at: string;
  status: 'active' | 'expired' | 'used';
  signature: string;
  verified: boolean;
}

interface ApiResponse {
  prescription: Prescription;
}

const ThemedText = ({ children, style, ...props }: any) => (
  <Text style={[{ color: PatientTheme.colors.text }, style]} {...props}>
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

export default function PrescriptionDetailScreen() {
  const { id } = useLocalSearchParams();
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadPrescription = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const result = await (api.getPrescription as any)(id);
      const data: ApiResponse = result || { prescription: null };
      setPrescription(data.prescription || null);
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

  const handleRetry = () => {
    loadPrescription();
  };

  const handleShare = () => {
    if (prescription) {
      router.push(`/patient/prescriptions/${prescription.id}/share`);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    if (status === 'active') return PatientTheme.colors.success;
    if (status === 'expired') return PatientTheme.colors.error;
    return '#6B7280';
  };

  const getStatusBadgeText = (status: string) => {
    if (status === 'active') return 'ACTIVE';
    if (status === 'expired') return 'EXPIRED';
    return 'USED';
  };

  // Loading state
  if (loading) {
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

  if (!prescription) {
    return (
      <View style={styles.centerContainer}>
        <ThemedText style={styles.emptyText}>Prescription not found</ThemedText>
      </View>
    );
  }

  const issueDate = prescription.created_at.split('T')[0];
  const expiryDate = prescription.expires_at.split('T')[0];

  const shortenedDid = prescription.doctor_did.length > 15
    ? `...${prescription.doctor_did.slice(-15)}`
    : prescription.doctor_did;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <View style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Recipient Details</ThemedText>
        <View style={styles.infoCard}>
          <ThemedText style={styles.value}>
            {prescription.patient_name}{'\n'}ID: {prescription.patient_id}{'\n'}Prescription: {prescription.id}
          </ThemedText>
        </View>
      </View>

      <View style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Prescribed By</ThemedText>
        <View style={styles.infoCard}>
          <ThemedText style={styles.label}>Doctor</ThemedText>
          <ThemedText style={styles.value}>{prescription.doctor_name}</ThemedText>

          <ThemedText style={[styles.label, { marginTop: PatientTheme.spacing.md }]}>
            DID
          </ThemedText>
          <ThemedText style={styles.value}>{shortenedDid}</ThemedText>

          {prescription.verified && (
            <View style={styles.verificationBadge} testID="verification-badge">
              <ThemedText style={styles.verificationText}>✓ Verified Signature</ThemedText>
            </View>
          )}
        </View>
      </View>

      <View style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Prescription Dates</ThemedText>
        <View style={styles.infoCard}>
          <View style={styles.statusRow}>
            <View
              style={[
                styles.statusBadge,
                { backgroundColor: getStatusBadgeColor(prescription.status) },
              ]}
              testID="status-badge"
            >
              <Text style={styles.statusBadgeText}>
                {getStatusBadgeText(prescription.status)}
              </Text>
            </View>
          </View>

          <ThemedText style={[styles.label, { marginTop: PatientTheme.spacing.md }]}>
            Issue Date: {issueDate}, Expiry: {expiryDate}
          </ThemedText>
        </View>
      </View>

      <View style={styles.section}>
        <ThemedText style={styles.sectionTitle}>Treatment Plan</ThemedText>
        <ThemedText style={styles.medicationsSummary}>
          {prescription.medications.map(m => m.name).join(', ')}
        </ThemedText>

        <ThemedText style={[styles.medicationDetail, { marginTop: PatientTheme.spacing.md }]}>
          {prescription.medications.map(m => `${m.dosage} ${m.frequency}`).join(', ')}
        </ThemedText>

        <ThemedText style={[styles.medicationDetail, { marginTop: PatientTheme.spacing.sm }]}>
          {prescription.medications.map(m => m.instructions).join('; ')}
        </ThemedText>
      </View>

      <View style={styles.actionSection}>
        <TouchableOpacity
          style={styles.shareButton}
          onPress={handleShare}
          testID="share-button"
        >
          <Text style={styles.shareButtonText}>Share Prescription with Pharmacist</Text>
        </TouchableOpacity>
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
  section: {
    marginBottom: PatientTheme.spacing.lg,
  },
  sectionTitle: {
    ...PatientTheme.typography.heading,
    marginBottom: PatientTheme.spacing.md,
    color: PatientTheme.colors.primary,
  },
  infoCard: {
    backgroundColor: PatientTheme.colors.surface,
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: PatientTheme.colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  value: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 4,
    color: PatientTheme.colors.text,
  },
  statusRow: {
    marginBottom: PatientTheme.spacing.md,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
  },
  statusBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
  },
  verificationBadge: {
    marginTop: PatientTheme.spacing.md,
    backgroundColor: '#ECFDF5',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: PatientTheme.colors.success,
  },
  verificationText: {
    color: PatientTheme.colors.success,
    fontSize: 13,
    fontWeight: '600',
  },
  medicationCard: {
    backgroundColor: PatientTheme.colors.surface,
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    marginBottom: PatientTheme.spacing.md,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  medicationsContainer: {
    marginBottom: PatientTheme.spacing.lg,
  },
  medicationName: {
    fontSize: 16,
    fontWeight: '700',
    color: PatientTheme.colors.text,
    marginBottom: PatientTheme.spacing.md,
  },
  medicationsSummary: {
    fontSize: 14,
    fontWeight: '500',
    color: PatientTheme.colors.text,
    marginBottom: PatientTheme.spacing.md,
  },
  medicationDetail: {
    fontSize: 14,
    fontWeight: '500',
    color: PatientTheme.colors.text,
    marginBottom: 6,
  },
  actionSection: {
    marginTop: PatientTheme.spacing.lg,
    paddingBottom: PatientTheme.spacing.lg,
  },
  shareButton: {
    backgroundColor: PatientTheme.colors.primary,
    paddingVertical: PatientTheme.spacing.md,
    paddingHorizontal: PatientTheme.spacing.lg,
    borderRadius: 8,
    alignItems: 'center',
  },
  shareButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  button: {
    backgroundColor: PatientTheme.colors.primary,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: PatientTheme.spacing.md,
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
