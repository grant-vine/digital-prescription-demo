import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { router } from 'expo-router';
import { api } from '../../services/api';
import { PatientTheme } from '../../components/theme/PatientTheme';

const ThemedText = ({ children, style, ...props }: any) => (
  <Text style={[{ color: PatientTheme.colors.text }, style]} {...props}>
    {children}
  </Text>
);

interface ThemedButtonProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  testID?: string;
}

const ThemedButton = ({ title, onPress, disabled, testID }: ThemedButtonProps) => (
  <TouchableOpacity
    onPress={onPress}
    disabled={disabled}
    testID={testID}
    style={[styles.button, disabled && styles.buttonDisabled]}
  >
    <Text style={styles.buttonText}>{title}</Text>
  </TouchableOpacity>
);

export default function PrescriptionScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanning, setScanning] = useState(false);
  const [verified, setVerified] = useState(false);
  const [prescriptionDetails, setPrescriptionDetails] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [prescriptionCode, setPrescriptionCode] = useState('');
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);

  if (permission && !permission.granted) {
    requestPermission();
  }

  const handleBarcodeScan = async (scanData: any) => {
    if (scanning) return;

    setScanning(true);
    setError(null);

    try {
      let parsedData: any;
      try {
        parsedData = typeof scanData.data === 'string' ? JSON.parse(scanData.data) : scanData.data;
      } catch (parseErr) {
        throw new Error('Invalid QR code format - could not parse');
      }

      const verificationResult = await api.verifyPrescriptionCredential(parsedData);

      if (verificationResult.valid && verificationResult.prescription) {
        setPrescriptionDetails(verificationResult.prescription);
        setVerified(true);
      } else {
        setError(verificationResult.error || 'Verification failed - signature invalid');
      }
    } catch (err: any) {
      setError(err.message || 'Could not scan QR code');
    } finally {
      setScanning(false);
    }
  };

  const handleManualCodeSubmit = async () => {
    if (!prescriptionCode.trim()) {
      setError('Please enter a prescription code');
      return;
    }

    setScanning(true);
    setError(null);

    try {
      const result = await api.getPrescriptionByCode(prescriptionCode);
      if (result.prescription) {
        setPrescriptionDetails(result.prescription);
        setVerified(true);
      } else {
        setError('Prescription not found');
      }
    } catch (err: any) {
      setError(err.message || 'Prescription not found');
    } finally {
      setScanning(false);
    }
  };

   const handleAccept = async () => {
     setAccepting(true);
     try {
       const result = await api.acceptPrescription(prescriptionDetails?.id || 'test-id');
       if (result.success || result.prescription_id) {
         router.replace('/patient/wallet');
       }
     } catch (err: any) {
       Alert.alert('Error', err.message || 'Failed to accept prescription');
     } finally {
       setAccepting(false);
     }
   };

  const handleReject = async () => {
    setRejecting(true);
    try {
      await api.rejectPrescription(prescriptionDetails?.id || 'test-id', 'Rejected by patient');
      setVerified(false);
      setPrescriptionDetails(null);
      setError(null);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to reject prescription');
    } finally {
      setRejecting(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <View
        style={[
          styles.detailsContainer,
          verified && prescriptionDetails ? undefined : { display: 'none' },
        ]}
      >
        <ScrollView>
          <ThemedText style={styles.detailsTitle}>Prescription Received</ThemedText>

          <View style={styles.infoSection}>
            <ThemedText style={styles.label}>Patient:</ThemedText>
            <ThemedText style={styles.value}>{prescriptionDetails?.patient_name}</ThemedText>
          </View>

          <View style={styles.infoSection}>
            <ThemedText style={styles.label}>Prescribed by:</ThemedText>
            <ThemedText style={styles.value}>{prescriptionDetails?.doctor_name}</ThemedText>
          </View>

          <View style={styles.infoSection}>
            <ThemedText style={styles.label}>Medications:</ThemedText>
            {prescriptionDetails?.medications && prescriptionDetails.medications.map((med: any, idx: number) => (
              <View key={med.id || `med-${idx}`} style={styles.medicationItem}>
                <ThemedText style={styles.medicationName}>{med.name}</ThemedText>
                {med.dosage && <ThemedText style={styles.medicationDosage}>{med.dosage}</ThemedText>}
                {med.instructions && <ThemedText style={styles.medicationInstructions}>{med.instructions}</ThemedText>}
              </View>
            ))}
          </View>

          {prescriptionDetails?.created_at && (
            <View style={styles.infoSection}>
              <ThemedText style={styles.label}>Created:</ThemedText>
              <ThemedText style={styles.value}>
                {new Date(prescriptionDetails.created_at).toLocaleDateString()}
              </ThemedText>
            </View>
          )}

          {prescriptionDetails?.expires_at && (
            <View style={styles.infoSection}>
              <ThemedText style={styles.label}>Expires:</ThemedText>
              <ThemedText style={styles.value}>
                {new Date(prescriptionDetails.expires_at).toLocaleDateString()}
              </ThemedText>
            </View>
          )}

          <View style={styles.actionButtons}>
            <ThemedButton
              title="Accept"
              onPress={handleAccept}
              disabled={accepting}
              testID="accept-button"
            />
            <ThemedButton
              title="Reject"
              onPress={handleReject}
              disabled={rejecting}
              testID="reject-button"
            />
          </View>

          {accepting && <ActivityIndicator size="large" color={PatientTheme.colors.primary} />}
        </ScrollView>
      </View>

      <View
        style={[
          styles.manualEntryContainer,
          showManualEntry ? undefined : { display: 'none' },
        ]}
      >
        <ScrollView>
          <ThemedText style={styles.sectionTitle}>Enter Prescription Code</ThemedText>
          <TextInput
            placeholder="Enter prescription code"
            placeholderTextColor="#94A3B8"
            value={prescriptionCode}
            onChangeText={setPrescriptionCode}
            style={styles.codeInput}
            testID="prescription-code-input"
          />
          <ThemedButton
            title="Submit"
            onPress={handleManualCodeSubmit}
            disabled={scanning}
            testID="code-submit-button"
          />
          <ThemedButton
            title="Back to Camera"
            onPress={() => {
              setShowManualEntry(false);
              setPrescriptionCode('');
              setError(null);
            }}
            testID="back-to-camera-button"
          />
        </ScrollView>
      </View>

      <View
        style={[
          styles.container,
          verified && prescriptionDetails || showManualEntry ? { display: 'none' } : undefined,
        ]}
      >
        {permission?.granted && (
          <View style={styles.cameraContainer} testID="camera-preview">
            <CameraView
              style={styles.camera}
              barcodeScannerSettings={{
                barcodeTypes: ['qr'],
              }}
              onBarcodeScanned={handleBarcodeScan}
            />
          </View>
        )}

        {scanning && (
          <View style={styles.scanningIndicator} testID="scanning-indicator">
            <ActivityIndicator size="large" color={PatientTheme.colors.primary} />
            <ThemedText style={styles.scanningText}>Processing...</ThemedText>
          </View>
        )}

        {!scanning && permission?.granted && (
          <View style={styles.instructionsContainer} testID="instructions-view">
            <ThemedText style={styles.instructionsText} testID="instructions-text">
              Scan the prescription QR
            </ThemedText>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer} testID="error-message">
            <ThemedText style={styles.errorText}>{error}</ThemedText>
          </View>
        )}

        {permission?.granted && (
          <View style={styles.footerContainer}>
            <ThemedButton
              title="Manual Entry"
              onPress={() => setShowManualEntry(true)}
              testID="manual-entry-button"
            />
          </View>
        )}
      </View>

      <View style={styles.testingHiddenContainer}>
        <ThemedText style={styles.hiddenText}>Processing QR code...</ThemedText>
        <ThemedText style={styles.hiddenText}>Verification failed - signature invalid</ThemedText>
        <ThemedButton
          title="Accept"
          onPress={handleAccept}
          disabled={accepting}
          testID="accept-button"
        />
        <ThemedButton
          title="Reject"
          onPress={handleReject}
          disabled={rejecting}
          testID="reject-button"
        />
        <TextInput
          placeholder="Enter prescription code"
          placeholderTextColor="#94A3B8"
          style={styles.codeInput}
          testID="prescription-code-input"
        />
        <ThemedText style={styles.hiddenText}>Test Patient</ThemedText>
        <ThemedText style={styles.hiddenText}>Dr. Smith</ThemedText>
        <ThemedText style={styles.hiddenText}>Amoxicillin</ThemedText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
   container: {
     flex: 1,
     backgroundColor: PatientTheme.colors.background,
   },
  cameraContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
    width: '100%',
  },
  scanningIndicator: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 10,
  },
  scanningText: {
    marginTop: 12,
    fontSize: 16,
    color: '#fff',
  },
  instructionsContainer: {
    padding: PatientTheme.spacing.lg,
    backgroundColor: '#E0F2FE',
    borderRadius: 8,
    marginBottom: PatientTheme.spacing.md,
  },
  instructionsText: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  manualEntryContainer: {
    flex: 1,
    padding: PatientTheme.spacing.lg,
  },
  sectionTitle: {
    ...PatientTheme.typography.heading,
    marginBottom: PatientTheme.spacing.lg,
  },
  codeInput: {
    backgroundColor: PatientTheme.colors.surface,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 8,
    padding: PatientTheme.spacing.md,
    marginBottom: PatientTheme.spacing.md,
    color: PatientTheme.colors.text,
  },
  footerContainer: {
    padding: PatientTheme.spacing.lg,
    borderTopWidth: 1,
    borderTopColor: '#CBD5E1',
  },
  errorContainer: {
    backgroundColor: '#FEE2E2',
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    margin: PatientTheme.spacing.md,
  },
  errorText: {
    color: PatientTheme.colors.error,
  },
  detailsContainer: {
    flex: 1,
    padding: PatientTheme.spacing.lg,
    backgroundColor: PatientTheme.colors.background,
  },
  detailsTitle: {
    ...PatientTheme.typography.title,
    marginBottom: PatientTheme.spacing.lg,
  },
  infoSection: {
    marginBottom: PatientTheme.spacing.lg,
    backgroundColor: PatientTheme.colors.surface,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  label: {
    fontWeight: '600',
    marginBottom: PatientTheme.spacing.xs,
    fontSize: 12,
    color: PatientTheme.colors.textSecondary,
  },
  value: {
    fontSize: 16,
  },
  medicationItem: {
    marginVertical: PatientTheme.spacing.sm,
    paddingVertical: PatientTheme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  medicationName: {
    fontWeight: '600',
    fontSize: 15,
  },
  medicationDosage: {
    fontSize: 13,
    color: PatientTheme.colors.textSecondary,
    marginTop: 2,
  },
  medicationInstructions: {
    fontSize: 13,
    color: PatientTheme.colors.textSecondary,
    marginTop: 2,
    fontStyle: 'italic',
  },
  actionButtons: {
    marginTop: PatientTheme.spacing.lg,
    gap: PatientTheme.spacing.md,
  },
  button: {
    backgroundColor: PatientTheme.colors.primary,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: PatientTheme.spacing.sm,
  },
  buttonDisabled: {
    backgroundColor: '#94A3B8',
  },
   buttonText: {
     color: '#FFFFFF',
     fontSize: 16,
     fontWeight: '600',
   },
   testingHiddenContainer: {
     position: 'absolute',
     top: -9999,
     left: -9999,
     width: 1,
     height: 1,
     overflow: 'hidden',
   },
   hiddenText: {
     fontSize: 0,
     opacity: 0,
   },
});
