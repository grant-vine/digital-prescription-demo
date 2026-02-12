import { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { api } from '../../../../services/api';

// Pharmacist Theme - Green #059669 (Clinical Dispensing Role)
const PharmacistTheme = {
  colors: {
    primary: '#059669', // Green main actions
    background: '#F0FDF4', // Light green bg
    surface: '#FFFFFF', // White cards
    text: '#064E3B', // Dark green text
    error: '#DC2626', // Red errors
    success: '#059669', // Green success
    border: '#BBF7D0', // Light green borders
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
  },
  typography: {
    title: {
      fontSize: 24,
      fontWeight: 'bold' as const,
      color: '#064E3B',
    },
    heading: {
      fontSize: 18,
      fontWeight: '600' as const,
      color: '#064E3B',
    },
  },
};

const ThemedText = ({ children, style, ...props }: any) => (
  <Text style={[{ color: PharmacistTheme.colors.text }, style]} {...props}>
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

// Checkbox component for React Native
const Checkbox = ({ value, onValueChange, testID, label }: any) => (
  <View style={styles.checkboxContainer}>
    <TouchableOpacity
      style={[styles.checkbox, value && styles.checkboxChecked]}
      onPress={() => onValueChange(!value)}
      testID={testID}
    >
      {value && <Text style={styles.checkmark}>✓</Text>}
    </TouchableOpacity>
    <ThemedText style={styles.checkboxLabel}>{label}</ThemedText>
  </View>
);

export default function PharmacistDispenseScreen() {
  const { id } = useLocalSearchParams();
  const [loading, setLoading] = useState(true);
  const [dispensing, setDispensing] = useState(false);
  const [error, setError] = useState('');
  const [prescription, setPrescription] = useState<any>(null);
  const [success, setSuccess] = useState(false);

  // Preparation checklist state
  const [checklist, setChecklist] = useState({
    visualInspection: false,
    counseling: false,
    labelPrinting: false,
  });

  // Partial dispensing state
  const [partialMode, setPartialMode] = useState(false);
  const [selectedMeds, setSelectedMeds] = useState<string[]>([]);

  const loadPrescription = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const apiAny = api as any;
      const result = await apiAny.getVerifiedPrescription(id);
      setPrescription(result || null);
    } catch (err: any) {
      setError(err.message || 'Failed to load prescription');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadPrescription();
  }, [loadPrescription]);

  const handleDispense = useCallback(async () => {
    setDispensing(true);
    setError('');
    try {
      const apiAny = api as any;
      await apiAny.dispenseMedication(id);
      await apiAny.logDispensingAction({
        prescriptionId: id,
        action: 'dispensed',
        timestamp: new Date().toISOString(),
      });
      setSuccess(true);
      setTimeout(() => {
        router.back();
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Dispensing failed');
    } finally {
      setDispensing(false);
    }
  }, [id]);

  const handlePartialDispense = useCallback(async () => {
    if (selectedMeds.length === 0) {
      setError('Please select at least one medication');
      return;
    }
    setDispensing(true);
    setError('');
    try {
      const apiAny = api as any;
      await apiAny.partialDispense(id, selectedMeds);
      await apiAny.logDispensingAction({
        prescriptionId: id,
        action: 'partial',
        items: selectedMeds,
        timestamp: new Date().toISOString(),
      });
      setSuccess(true);
      setTimeout(() => {
        router.back();
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Partial dispensing failed');
    } finally {
      setDispensing(false);
    }
  }, [id, selectedMeds]);

  const handleRetry = useCallback(() => {
    setError('');
    loadPrescription();
  }, [loadPrescription]);

  const toggleMedicationSelection = useCallback((medName: string) => {
    setSelectedMeds((prev) => {
      if (prev.includes(medName)) {
        return prev.filter((m) => m !== medName);
      }
      return [...prev, medName];
    });
  }, []);

  // Loading state
  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator
          size="large"
          color={PharmacistTheme.colors.primary}
          testID="loading-spinner"
        />
        <ThemedText style={styles.loadingText}>Loading prescription...</ThemedText>
      </View>
    );
  }

  // Error state (no prescription loaded)
  if (error && !prescription) {
    const isInvalid =
      error.includes('invalid') ||
      error.includes('not found') ||
      error.includes('not exist');
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
      >
        <View
          style={styles.errorContainer}
          testID={isInvalid ? 'invalid-prescription-message' : 'error-message'}
        >
          <ThemedText style={styles.errorText}>Load Failed: {error}</ThemedText>
        </View>
        <ThemedButton title="Retry Load" onPress={handleRetry} testID="retry-button" />
        <ThemedButton title="Go Back" onPress={() => router.back()} />
      </ScrollView>
    );
  }

  // Success state
  if (success) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
      >
        <View style={styles.successContainer} testID="success-message">
          <Text style={styles.successIcon}>✓</Text>
          <ThemedText style={styles.successTitle}>
            Successfully Dispensed
          </ThemedText>
          <ThemedText style={styles.successSubtitle}>
            Prescription has been marked as dispensed
          </ThemedText>
        </View>
      </ScrollView>
    );
  }

  // Dispensing in progress
  if (dispensing) {
    return (
      <View style={styles.container}>
        <ActivityIndicator
          size="large"
          color={PharmacistTheme.colors.primary}
          testID="dispensing-spinner"
        />
        <ThemedText style={styles.loadingText}>Dispensing medication...</ThemedText>
      </View>
    );
  }

  // Main dispensing screen
  const allChecklistComplete =
    checklist.visualInspection &&
    checklist.counseling &&
    checklist.labelPrinting;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <ThemedText style={styles.title}>Pharmacist Workflow</ThemedText>

      {/* Prescription Display */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <ThemedText style={styles.cardTitle}>Prescription Details</ThemedText>
        </View>
        <View style={styles.cardContent}>
          <ThemedText testID="doctor-name">
            Prescribing Physician: Dr. {prescription?.credential?.issuer?.name || 'Unknown'}
          </ThemedText>
          <ThemedText testID="patient-name">
            For: {prescription?.credential?.credentialSubject?.name || 'Unknown Patient'}
          </ThemedText>
          <View style={styles.verificationBadge} testID="verification-badge">
            <ThemedText style={styles.verificationText}>✓ Authenticated</ThemedText>
          </View>
        </View>
      </View>

      {/* Medication List */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <ThemedText style={styles.cardTitle}>Medications</ThemedText>
        </View>
        <View style={styles.cardContent} testID="medication-list">
          <ThemedText testID="medication-details">
            {prescription?.credential?.credentialSubject?.prescription?.medications
              ?.map((m: any) => `${m.drug_name} ${m.dosage} qty=${m.quantity}`)
              .join(', ') || 'No medications'}
          </ThemedText>
          <ThemedText style={styles.instructionsText} testID="instructions">
            {prescription?.credential?.credentialSubject?.prescription?.medications
              ?.map((m: any) => `Instructions: ${m.instructions}`)
              .join('; ') || 'No instructions'}
          </ThemedText>
          {partialMode && (
            <View testID="medication-selector">
              <ThemedText style={styles.selectorTitle}>
                Select medications to dispense:
              </ThemedText>
              {prescription?.credential?.credentialSubject?.prescription?.medications?.map(
                (med: any) => (
                  <Checkbox
                    key={med.drug_name}
                    value={selectedMeds.includes(med.drug_name)}
                    onValueChange={() => toggleMedicationSelection(med.drug_name)}
                    label={`Include ${med.drug_name}`}
                    testID={`select-${med.drug_name.toLowerCase()}`}
                  />
                )
              )}
            </View>
          )}
        </View>
      </View>

      {/* Preparation Checklist */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <ThemedText style={styles.cardTitle}>Preparation Checklist</ThemedText>
        </View>
        <View style={styles.cardContent}>
          <Checkbox
            value={checklist.visualInspection}
            onValueChange={(val: boolean) =>
              setChecklist({ ...checklist, visualInspection: val })
            }
            label="Visual inspection completed"
            testID="visual-inspection-checkbox"
          />
          <Checkbox
            value={checklist.counseling}
            onValueChange={(val: boolean) =>
              setChecklist({ ...checklist, counseling: val })
            }
            label="Patient counseling provided"
            testID="counseling-checkbox"
          />
          <Checkbox
            value={checklist.labelPrinting}
            onValueChange={(val: boolean) =>
              setChecklist({ ...checklist, labelPrinting: val })
            }
            label="Labels printed"
            testID="label-printing-checkbox"
          />
        </View>
      </View>

      {/* Error Display */}
      {error && (
        <View style={styles.errorContainer} testID="dispensing-error-message">
          <ThemedText style={styles.errorText}>Dispensing Error: {error}</ThemedText>
          <ThemedButton
            title="Dismiss Error"
            onPress={() => setError('')}
            testID="retry-button"
          />
        </View>
      )}

      {/* Dispensing Actions */}
      <View style={styles.actionsContainer}>
        {!partialMode ? (
          <>
            <ThemedButton
              title="Mark as Complete"
              onPress={handleDispense}
              disabled={!allChecklistComplete}
              testID="dispense-button"
            />
            <ThemedButton
              title="Partial Dispense"
              onPress={() => setPartialMode(true)}
              testID="partial-dispense-button"
            />
          </>
        ) : (
          <>
            <ThemedButton
              title="Confirm Selection"
              onPress={handlePartialDispense}
              disabled={selectedMeds.length === 0}
              testID="confirm-partial-dispense-button"
            />
            <ThemedButton
              title="Cancel"
              onPress={() => {
                setPartialMode(false);
                setSelectedMeds([]);
              }}
            />
          </>
        )}
      </View>

      {/* Back Button */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.back()}
        testID="back-button"
      >
        <ThemedText style={styles.backButtonText}>← Back</ThemedText>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: PharmacistTheme.colors.background,
  },
  contentContainer: {
    padding: PharmacistTheme.spacing.lg,
  },
  title: {
    ...PharmacistTheme.typography.title,
    marginBottom: PharmacistTheme.spacing.lg,
    textAlign: 'center',
  },
  card: {
    backgroundColor: PharmacistTheme.colors.surface,
    borderRadius: 12,
    marginBottom: PharmacistTheme.spacing.lg,
    borderWidth: 1,
    borderColor: PharmacistTheme.colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    padding: PharmacistTheme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: PharmacistTheme.colors.border,
  },
  cardTitle: {
    ...PharmacistTheme.typography.heading,
    fontSize: 16,
  },
  cardContent: {
    padding: PharmacistTheme.spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: PharmacistTheme.spacing.sm,
    alignItems: 'center',
  },
  label: {
    fontWeight: '600',
    marginRight: PharmacistTheme.spacing.sm,
    width: 80,
  },
  value: {
    flex: 1,
  },
  verificationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: PharmacistTheme.spacing.md,
    paddingVertical: PharmacistTheme.spacing.sm,
    borderRadius: 6,
    marginTop: PharmacistTheme.spacing.md,
    alignSelf: 'flex-start',
  },
  verificationIcon: {
    color: PharmacistTheme.colors.success,
    fontSize: 16,
    marginRight: PharmacistTheme.spacing.xs,
  },
  verificationText: {
    color: PharmacistTheme.colors.success,
    fontWeight: '600',
  },
  medicationItem: {
    borderBottomWidth: 1,
    borderBottomColor: PharmacistTheme.colors.border,
    paddingVertical: PharmacistTheme.spacing.md,
  },
  medicationSummary: {
    fontSize: 14,
    marginBottom: PharmacistTheme.spacing.md,
    fontWeight: '600',
  },
  medicationName: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: PharmacistTheme.spacing.sm,
    color: PharmacistTheme.colors.primary,
  },
  medicationDetails: {
    marginBottom: PharmacistTheme.spacing.sm,
  },
  medicationDetailText: {
    fontSize: 14,
    marginBottom: 2,
    color: '#64748B',
  },
  instructionsContainer: {
    backgroundColor: '#F8FAFC',
    padding: PharmacistTheme.spacing.sm,
    borderRadius: 6,
    marginTop: PharmacistTheme.spacing.sm,
  },
  instructionsLabel: {
    fontWeight: '600',
    fontSize: 13,
    marginBottom: 4,
  },
  instructionsText: {
    fontSize: 13,
    lineHeight: 18,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: PharmacistTheme.spacing.md,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: PharmacistTheme.colors.primary,
    borderRadius: 4,
    marginRight: PharmacistTheme.spacing.sm,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: PharmacistTheme.colors.surface,
  },
  checkboxChecked: {
    backgroundColor: PharmacistTheme.colors.primary,
  },
  checkmark: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    fontSize: 14,
    flex: 1,
  },
  actionsContainer: {
    marginVertical: PharmacistTheme.spacing.lg,
  },
  medicationSelectorHeader: {
    marginBottom: PharmacistTheme.spacing.md,
  },
  selectorTitle: {
    ...PharmacistTheme.typography.heading,
    fontSize: 16,
  },
  button: {
    backgroundColor: PharmacistTheme.colors.primary,
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: PharmacistTheme.spacing.sm,
  },
  buttonDisabled: {
    backgroundColor: '#94A3B8',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    marginTop: PharmacistTheme.spacing.lg,
    padding: PharmacistTheme.spacing.sm,
  },
  backButtonText: {
    color: PharmacistTheme.colors.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: PharmacistTheme.spacing.md,
    fontSize: 14,
  },
  errorTitle: {
    ...PharmacistTheme.typography.title,
    color: PharmacistTheme.colors.error,
    marginBottom: PharmacistTheme.spacing.lg,
    textAlign: 'center',
  },
  errorContainer: {
    backgroundColor: '#FEE2E2',
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PharmacistTheme.spacing.lg,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  errorText: {
    color: PharmacistTheme.colors.error,
    fontSize: 14,
    marginBottom: PharmacistTheme.spacing.sm,
  },
  successContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: PharmacistTheme.spacing.xl * 2,
  },
  successIcon: {
    fontSize: 72,
    color: PharmacistTheme.colors.success,
    marginBottom: PharmacistTheme.spacing.lg,
  },
  successTitle: {
    ...PharmacistTheme.typography.title,
    color: PharmacistTheme.colors.success,
    marginBottom: PharmacistTheme.spacing.sm,
    textAlign: 'center',
  },
  successSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    color: '#64748B',
  },
});
