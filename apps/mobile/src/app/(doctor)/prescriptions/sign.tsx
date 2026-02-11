import { useEffect, useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { api, PrescriptionDraft } from '../../../services/api';
import { DoctorTheme } from '../../../components/theme/DoctorTheme';

const ThemedText = ({ children, style, ...props }: any) => (
  <Text style={[{ color: DoctorTheme.colors.text, ...DoctorTheme.typography.body }, style]} {...props}>
    {children}
  </Text>
);

const ThemedButton = ({ title, onPress, disabled, variant = 'primary', style, testID }: any) => (
  <TouchableOpacity
    onPress={onPress}
    disabled={disabled}
    style={[
      {
        backgroundColor: disabled 
          ? '#94A3B8' 
          : variant === 'primary' 
            ? DoctorTheme.colors.primary 
            : '#E2E8F0',
        padding: DoctorTheme.spacing.md,
        borderRadius: 8,
        alignItems: 'center',
      },
      style,
    ]}
    testID={testID}
  >
    <Text style={{ color: variant === 'primary' ? '#FFFFFF' : DoctorTheme.colors.text, fontSize: 16, fontWeight: '600' }}>
      {title}
    </Text>
  </TouchableOpacity>
);

export default function PrescriptionSignScreen() {
  const router = useRouter();
  const { prescriptionId } = useLocalSearchParams<{ prescriptionId: string }>();
  
  const [draft, setDraft] = useState<PrescriptionDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [signing, setSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const loadDraft = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPrescriptionDraft(prescriptionId as string);
      setDraft(data);
    } catch (err) {
      setError('Failed to load prescription draft');
    } finally {
      setLoading(false);
    }
  }, [prescriptionId]);

  useEffect(() => {
    if (prescriptionId) {
      loadDraft();
    }
  }, [prescriptionId, loadDraft]);

  const handleSignPrescription = async () => {
    try {
      setSigning(true);
      setError(null);
      const result = await api.signPrescription(prescriptionId as string);
      setSuccess(true);
      // Navigate to QR display after brief success message
      setTimeout(() => {
        router.push(`/(doctor)/prescriptions/qr-display?prescriptionId=${result.prescription_id}`);
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Failed to sign prescription');
    } finally {
      setSigning(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <ThemedText style={styles.title}>
          Review Prescription
        </ThemedText>

        {loading && !draft && <ActivityIndicator size="large" color={DoctorTheme.colors.primary} style={{ marginTop: 20 }} />}

        {draft && (
          <View style={styles.section}>
            <ThemedText style={styles.sectionTitle}>
              Prescription Review
            </ThemedText>
            
            <View style={styles.row}>
              <ThemedText style={styles.label}>Patient:</ThemedText>
              <ThemedText>{draft.patient_name}</ThemedText>
            </View>

            <View style={styles.row}>
              <ThemedText style={styles.label}>Medications:</ThemedText>
              <ThemedText>
                {draft.medications.map(m => `${m.name} - ${m.dosage} (${m.instructions})`).join('\n')}
              </ThemedText>
            </View>

            {draft.repeat_count > 0 && (
              <View style={styles.row}>
                <ThemedText style={styles.label}>Repeats:</ThemedText>
                <ThemedText>{draft.repeat_count} repeat(s) every {draft.repeat_interval}</ThemedText>
              </View>
            )}
          </View>
        )}

        <View style={styles.disclaimer}>
          <ThemedText style={styles.disclaimerTitle}>
            Legal Disclaimer
          </ThemedText>
          <ThemedText style={styles.disclaimerText}>
            By confirming, you verify this prescription. This action is legally binding 
            and verifies that you have reviewed and approved this prescription for the patient.
          </ThemedText>
        </View>

        {error && (
          <View style={styles.errorContainer} testID="error-message">
            <ThemedText style={styles.errorText}>{error}</ThemedText>
          </View>
        )}

        {success && (
          <View style={styles.successContainer} testID="success-message">
            <ThemedText style={styles.successText}>Prescription signed successfully!</ThemedText>
          </View>
        )}

        <ThemedButton
          title={signing ? "Signing..." : error ? "Retry Sign Prescription" : "Proceed"}
          onPress={handleSignPrescription}
          disabled={signing || success}
          testID="confirm-sign-button"
          style={{ marginTop: 16 }}
        />

        {signing && (
          <ActivityIndicator size="small" color={DoctorTheme.colors.primary} style={{ marginTop: 16 }} testID="loading-indicator" />
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DoctorTheme.colors.background,
  },
  content: {
    padding: DoctorTheme.spacing.lg,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  row: {
    marginBottom: 16,
  },
  label: {
    fontWeight: '600',
    marginBottom: 4,
  },
  medicationItem: {
    marginLeft: 16,
    marginBottom: 8,
    paddingLeft: 8,
    borderLeftWidth: 2,
    borderLeftColor: DoctorTheme.colors.primary,
  },
  medicationDetail: {
    fontSize: 14,
    color: '#64748B',
  },
  disclaimer: {
    backgroundColor: '#FEF3C7',
    padding: 16,
    borderRadius: 8,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#FCD34D',
  },
  disclaimerTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#92400E',
  },
  disclaimerText: {
    fontSize: 14,
    color: '#92400E',
  },
  errorContainer: {
    backgroundColor: '#FEE2E2',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  errorText: {
    color: '#DC2626',
  },
  successContainer: {
    backgroundColor: '#D1FAE5',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#6EE7B7',
  },
  successText: {
    color: '#059669',
    fontWeight: '600',
  },
});
