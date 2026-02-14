import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import QRCode from 'react-native-qrcode-svg';

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

export interface QRDisplayProps {
  data: VerifiableCredential | null | undefined;
  size?: number;
  onRefresh?: () => void;
}

export default function QRDisplay({ data, size = 300, onRefresh }: QRDisplayProps) {
  if (!data) return null;
  
  const qrValue = JSON.stringify(data);
  
  return (
    <View style={styles.container}>
      <QRCode 
        value={qrValue}
        size={size}
        color="black"
        backgroundColor="white"
      />
      {onRefresh && (
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Text style={styles.refreshText}>Refresh</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
  },
  refreshButton: {
    marginTop: 20,
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  refreshText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});
