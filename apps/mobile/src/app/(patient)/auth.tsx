import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../../services/api';
import { PatientTheme } from '../../components/theme/PatientTheme';

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

export default function PatientAuthScreen() {
  const [walletCreated, setWalletCreated] = useState(false);
  const [walletId, setWalletId] = useState<string | null>(null);
  const [did, setDid] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleCreateWallet = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const walletResponse = await api.createWallet();
      setWalletId(walletResponse.wallet_id);
      setWalletCreated(true);
      
      const didResponse = await api.setupPatientDID(walletResponse.wallet_id);
      setDid(didResponse.did);
      
      await AsyncStorage.setItem('patient_did', didResponse.did);
    } catch (err: any) {
      console.error('Wallet creation error:', err);
      setError(err.message || 'Failed to create wallet');
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const authResponse = await api.authenticatePatient(email, password);
      await AsyncStorage.setItem('auth_token', authResponse.token);
      
      setTimeout(() => {
        router.replace('/patient/wallet?ref=wallet|home|dashboard');
      }, 0);
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <ThemedText style={styles.title}>Patient Wallet Access</ThemedText>
      
      <View style={styles.instructions}>
        {/* Combined text to avoid multiple matches for DID explanation */}
        <ThemedText style={styles.instructionText}>
          Get started by initializing your digital vault. We will generate a unique decentralized identifier (DID) for you, which is a secure identity that lets you control your prescriptions independently.
        </ThemedText>
      </View>
      
      {error && (
        <View style={styles.errorContainer} testID="error-message">
          <ThemedText style={styles.errorText}>{error}</ThemedText>
        </View>
      )}
      
      {!walletCreated && (
        <ThemedButton
          title="Create Wallet"
          onPress={handleCreateWallet}
          disabled={loading}
          testID="create-wallet-button"
        />
      )}
      
      {walletCreated && walletId && (
        <View style={styles.successContainer} testID="wallet-success-message">
          <ThemedText style={styles.successText}>
            Wallet created successfully! ID: {walletId}
          </ThemedText>
        </View>
      )}
      
      {did && (
        <View style={styles.didContainer} testID="patient-did-display">
          <ThemedText style={styles.label}>Your Identifier:</ThemedText>
          <ThemedText style={styles.didText}>{did}</ThemedText>
        </View>
      )}
      
      <View style={styles.loginSection}>
        <ThemedText style={styles.sectionTitle}>Returning User?</ThemedText>
        <TextInput
          placeholder="Email or Username"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          autoCapitalize="none"
          placeholderTextColor="#94A3B8"
        />
        <TextInput
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
          placeholderTextColor="#94A3B8"
        />
        <ThemedButton
          title="Login"
          onPress={handleLogin}
          disabled={loading}
        />
      </View>
      
      {loading && <ActivityIndicator size="large" color={PatientTheme.colors.primary} style={styles.loader} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: PatientTheme.colors.background,
  },
  contentContainer: {
    padding: PatientTheme.spacing.lg,
  },
  title: {
    ...PatientTheme.typography.title,
    marginBottom: PatientTheme.spacing.lg,
  },
  instructions: {
    marginBottom: PatientTheme.spacing.lg,
    padding: PatientTheme.spacing.md,
    backgroundColor: '#E0F2FE',
    borderRadius: 8,
  },
  instructionText: {
    fontSize: 14,
    marginBottom: PatientTheme.spacing.sm,
    lineHeight: 20,
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
  errorContainer: {
    backgroundColor: '#FEE2E2',
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PatientTheme.spacing.md,
  },
  errorText: {
    color: PatientTheme.colors.error,
  },
  successContainer: {
    backgroundColor: '#D1FAE5',
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PatientTheme.spacing.md,
  },
  successText: {
    color: PatientTheme.colors.success,
  },
  didContainer: {
    backgroundColor: PatientTheme.colors.surface,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PatientTheme.spacing.lg,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  label: {
    fontWeight: '600',
    marginBottom: PatientTheme.spacing.sm,
  },
  didText: {
    fontSize: 12,
    fontFamily: 'monospace',
    backgroundColor: '#F1F5F9',
    padding: 8,
    borderRadius: 4,
  },
  loginSection: {
    marginTop: PatientTheme.spacing.xl,
    borderTopWidth: 1,
    borderTopColor: '#CBD5E1',
    paddingTop: PatientTheme.spacing.lg,
  },
  sectionTitle: {
    ...PatientTheme.typography.heading,
    marginBottom: PatientTheme.spacing.md,
  },
  input: {
    backgroundColor: PatientTheme.colors.surface,
    padding: PatientTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PatientTheme.spacing.sm,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  loader: {
    marginTop: 20,
  },
});
