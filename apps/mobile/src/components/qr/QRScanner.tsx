import { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export interface VerifiableCredential {
  '@context'?: string[];
  type: string[];
  issuer: string;
  credentialSubject: {
    prescriptionId: string;
    patientName: string;
    medications: Array<{
      name: string;
      dosage: string;
      frequency: string;
    }>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface QRScannerProps {
  onQRCodeScanned: (credential: VerifiableCredential) => void;
  onError?: (error: Error) => void;
}

export default function QRScanner({ onQRCodeScanned, onError }: QRScannerProps) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Point camera at QR code');

  useEffect(() => {
    if (permission?.granted === false) {
      const error = new Error('Camera permission denied');
      error.name = 'PERMISSION_DENIED';
      onError?.(error);
    } else if (permission?.granted === undefined) {
      requestPermission();
    }
  }, [permission, requestPermission, onError]);

  const handleBarCodeScanned = ({ data }: { data: string; type: string }) => {
    if (scanned) return;
    
    setScanned(true);
    setStatusMessage('Processing prescription...');

    try {
      const credential = JSON.parse(data);

      if (!credential.type || !Array.isArray(credential.type)) {
        throw Object.assign(new Error('Invalid credential type'), {
          name: 'INVALID_CREDENTIAL_TYPE',
        });
      }

      if (!credential.type.includes('VerifiableCredential')) {
        throw Object.assign(new Error('This is not a valid prescription'), {
          name: 'INVALID_CREDENTIAL_TYPE',
        });
      }

      if (!credential.issuer) {
        throw Object.assign(new Error('Incomplete prescription data'), {
          name: 'MISSING_FIELD',
          field: 'issuer',
        });
      }

      if (!credential.credentialSubject) {
        throw Object.assign(new Error('Incomplete prescription data'), {
          name: 'MISSING_FIELD',
          field: 'credentialSubject',
        });
      }

      setStatusMessage('Prescription loaded');
      onQRCodeScanned(credential as VerifiableCredential);
    } catch (error) {
      if (error instanceof SyntaxError) {
        const jsonError = new Error('Invalid QR code format');
        jsonError.name = 'INVALID_JSON';
        onError?.(jsonError);
      } else {
        onError?.(error as Error);
      }
      setScanned(false);
      setStatusMessage('Point camera at QR code');
    }
  };

  if (permission?.granted === false) {
    return (
      <View style={styles.container} testID="permission-error">
        <Text style={styles.errorText}>Camera permission denied</Text>
      </View>
    );
  }

  if (!permission?.granted) {
    return (
      <View style={styles.container} testID="loading">
        <Text>Requesting camera permission...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        testID="camera-component"
        style={styles.camera}
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
        barcodeScannerSettings={{
          barcodeTypes: ['qr'],
        }}
      />
      <View style={styles.overlay}>
        <Text style={styles.statusText}>{statusMessage}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  camera: {
    flex: 1,
    width: '100%',
  },
  overlay: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  statusText: {
    fontSize: 16,
    color: 'white',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  errorText: {
    fontSize: 16,
    color: 'red',
    textAlign: 'center',
  },
});
