import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DoctorTheme } from '../../../components/theme/DoctorTheme';

export default function DoctorScanQRScreen(): React.ReactElement {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.icon}>📷</Text>
        <Text style={styles.title}>Scan Patient QR Code</Text>
        <Text style={styles.description}>
          This feature allows you to scan a patient's QR code to quickly load their information.
        </Text>
        <Text style={styles.note}>
          (Mock implementation for demo purposes)
        </Text>
        
        <TouchableOpacity
          style={styles.button}
          onPress={() => router.back()}
          testID="back-button"
        >
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DoctorTheme.colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  icon: {
    fontSize: 64,
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: DoctorTheme.colors.text,
    marginBottom: 12,
    textAlign: 'center',
  },
  description: {
    fontSize: 16,
    color: DoctorTheme.colors.textSecondary,
    textAlign: 'center',
    marginBottom: 8,
    lineHeight: 22,
  },
  note: {
    fontSize: 14,
    color: DoctorTheme.colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 32,
  },
  button: {
    backgroundColor: DoctorTheme.colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
