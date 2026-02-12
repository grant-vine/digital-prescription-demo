import { useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../../services/api';

// Pharmacist Theme - Green #059669 (Clinical Dispensing Role)
const PharmacistTheme = {
  colors: {
    primary: '#059669',      // Green main actions
    background: '#F0FDF4',   // Light green bg
    surface: '#FFFFFF',      // White cards
    text: '#064E3B',        // Dark green text
    error: '#DC2626',       // Red errors
    success: '#059669',     // Green success
  },
  spacing: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
  },
  typography: {
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      color: '#064E3B',
    },
    heading: {
      fontSize: 18,
      fontWeight: '600',
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

enum AuthStep {
  LOGIN = 'login',
  PROFILE_SETUP = 'profile',
  SAPC_VALIDATION = 'sapc',
  DID_CREATION = 'did',
  COMPLETE = 'complete'
}

export default function PharmacistAuthScreen() {
  const [currentStep, setCurrentStep] = useState<AuthStep>(AuthStep.LOGIN);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Login state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pharmacistId, setPharmacistId] = useState<string | null>(null);
  
  // Profile setup state
  const [pharmacyName, setPharmacyName] = useState('');
  const [sapcNumber, setSAPCNumber] = useState('');
  const [sapcValidated, setSAPCValidated] = useState(false);
  const [sapcError, setSAPCError] = useState<string | null>(null);
  
  // DID state
  const [did, setDid] = useState<string | null>(null);
  
  const handleLogin = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      await Promise.resolve(); // Defer to next tick for test mocks
      const authResponse = await api.authenticatePharmacist(email, password);
      
      setPharmacistId(authResponse.pharmacist.id);
      await AsyncStorage.setItem('auth_token', authResponse.token);
      
      setCurrentStep(AuthStep.PROFILE_SETUP);
      router.replace('/(pharmacist)/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }, [email, password]);
  
  const handleValidateSAPC = useCallback(async () => {
    try {
      setLoading(true);
      setSAPCError(null);
      
      await Promise.resolve(); // Defer to next tick for test mocks
      const validationResponse = await api.validateSAPC(sapcNumber);
      
      setSAPCValidated(true);
      setCurrentStep(AuthStep.DID_CREATION);
    } catch (err: any) {
      console.error('SAPC validation error:', err);
      setSAPCError(err.message || 'SAPC validation failed');
    } finally {
      setLoading(false);
    }
  }, [sapcNumber]);
  
   const handleSetupPharmacy = useCallback(async () => {
     try {
       setLoading(true);
       setError(null);
       
       await Promise.resolve(); // Defer to next tick for test mocks
       const setupResponse = await api.setupPharmacy({
         pharmacy_name: pharmacyName,
         sapc_number: sapcNumber,
       });
       
       // Auto-progress: validate SAPC, then create DID
       setCurrentStep(AuthStep.SAPC_VALIDATION);
       
       // Automatically validate SAPC after setup
       const validationResponse = await api.validateSAPC(sapcNumber);
       setSAPCValidated(true);
       
       // Automatically create DID after SAPC validation
       if (pharmacistId) {
         const didResponse = await api.createPharmacistDID(pharmacistId);
         setDid(didResponse.did);
         await AsyncStorage.setItem('pharmacist_did', didResponse.did);
         setCurrentStep(AuthStep.COMPLETE);
       }
     } catch (err: any) {
       console.error('Pharmacy setup error:', err);
       setError(err.message || 'Pharmacy setup failed');
     } finally {
       setLoading(false);
     }
   }, [pharmacyName, sapcNumber, pharmacistId]);
  
  const handleCreateDID = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!pharmacistId) {
        setError('Pharmacist ID not available');
        return;
      }
      
      await Promise.resolve(); // Defer to next tick for test mocks
      const didResponse = await api.createPharmacistDID(pharmacistId);
      
      setDid(didResponse.did);
      await AsyncStorage.setItem('pharmacist_did', didResponse.did);
      
      setCurrentStep(AuthStep.COMPLETE);
      
      router.replace('/pharmacist/dashboard');
    } catch (err: any) {
      console.error('DID creation error:', err);
      setError(err.message || 'DID creation failed');
    } finally {
      setLoading(false);
    }
  }, [pharmacistId]);
  
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <ThemedText style={styles.title}>Pharmacy Onboarding</ThemedText>
      
       <View style={styles.instructions}>
         <ThemedText style={styles.instructionText}>
           Welcome to the Pharmacy Management System. Set up your pharmacy profile and review your South African Pharmacy Council (SAPC) registration details. This ensures secure and compliant digital prescription management.
         </ThemedText>
       </View>
      
      {error && (
        <View style={styles.errorContainer} testID="error-message">
          <ThemedText style={styles.errorText}>{error}</ThemedText>
          {error && (
            <ThemedButton
              title="Retry"
              onPress={() => {
                setError(null);
                if (currentStep === AuthStep.LOGIN) handleLogin();
                else if (currentStep === AuthStep.PROFILE_SETUP) handleSetupPharmacy();
                else if (currentStep === AuthStep.DID_CREATION) handleCreateDID();
              }}
              disabled={loading}
            />
          )}
        </View>
      )}
      
      {/* LOGIN FORM */}
      {currentStep === AuthStep.LOGIN && (
        <View style={styles.formSection}>
          <ThemedText style={styles.sectionTitle}>Credentials</ThemedText>
          <TextInput
            placeholder="Email or Account Username"
            value={email}
            onChangeText={setEmail}
            style={styles.input}
            autoCapitalize="none"
            editable={!loading}
            placeholderTextColor="#94A3B8"
          />
          <TextInput
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            style={styles.input}
            editable={!loading}
            placeholderTextColor="#94A3B8"
          />
          <ThemedButton
            title="Authenticate"
            onPress={handleLogin}
            disabled={loading || !email || !password}
            testID="login-button"
          />
        </View>
      )}
      
       {/* PHARMACY PROFILE SETUP - Always visible and editable */}
       <View style={styles.formSection}>
         <ThemedText style={styles.sectionTitle}>Pharmacy Details</ThemedText>
         <TextInput
           placeholder="Pharmacy Name"
           value={pharmacyName}
           onChangeText={setPharmacyName}
           style={styles.input}
           editable={!loading}
           placeholderTextColor="#94A3B8"
         />
         <TextInput
           placeholder="SAPC Registration Number"
           value={sapcNumber}
           onChangeText={setSAPCNumber}
           style={styles.input}
           editable={!loading}
           placeholderTextColor="#94A3B8"
         />
        
        <ThemedButton
          title="Submit"
          onPress={handleSetupPharmacy}
          disabled={loading || !pharmacyName || !sapcNumber}
          testID="submit-profile-button"
        />
      </View>
      
      {/* SAPC VALIDATION SECTION - Always visible */}
      <View style={styles.formSection}>
        <ThemedText style={styles.sectionTitle}>SAPC Registration</ThemedText>
        
        <ThemedButton
          title="Verify"
          onPress={handleValidateSAPC}
          disabled={loading || !sapcNumber}
          testID="validate-sapc-button"
        />
        
        {sapcError && (
          <View style={styles.errorContainer} testID="sapc-error-message">
            <ThemedText style={styles.errorText}>{sapcError}</ThemedText>
          </View>
        )}
        
        {sapcValidated && !sapcError && (
          <View style={styles.successContainer} testID="sapc-success-message">
            <ThemedText style={styles.successText}>
              Registration verified and registered.
            </ThemedText>
          </View>
        )}
      </View>
      
       {/* DID CREATION SECTION - Always visible */}
       <View style={styles.formSection}>
         <ThemedText style={styles.sectionTitle}>Decentralized Identity</ThemedText>
        
        {!did && (
          <ThemedButton
            title="Create DID"
            onPress={handleCreateDID}
            disabled={loading || !pharmacistId}
            testID="generate-did-button"
          />
        )}
        
        {did && (
          <View style={styles.didContainer} testID="pharmacist-did-display">
            <ThemedText style={styles.label}>Your Decentralized Identifier:</ThemedText>
            <ThemedText style={styles.didText}>{did}</ThemedText>
          </View>
        )}
      </View>
      
      {loading && <ActivityIndicator size="large" color={PharmacistTheme.colors.primary} style={styles.loader} />}
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
  },
  instructions: {
    marginBottom: PharmacistTheme.spacing.lg,
    padding: PharmacistTheme.spacing.md,
    backgroundColor: '#DBEAFE',
    borderRadius: 8,
  },
  instructionText: {
    fontSize: 14,
    marginBottom: PharmacistTheme.spacing.sm,
    lineHeight: 20,
  },
  formSection: {
    marginBottom: PharmacistTheme.spacing.xl,
  },
  sectionTitle: {
    ...PharmacistTheme.typography.heading,
    marginBottom: PharmacistTheme.spacing.md,
  },
  input: {
    backgroundColor: PharmacistTheme.colors.surface,
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PharmacistTheme.spacing.sm,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    color: PharmacistTheme.colors.text,
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
  errorContainer: {
    backgroundColor: '#FEE2E2',
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PharmacistTheme.spacing.md,
  },
  errorText: {
    color: PharmacistTheme.colors.error,
    marginBottom: PharmacistTheme.spacing.sm,
  },
  successContainer: {
    backgroundColor: '#D1FAE5',
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PharmacistTheme.spacing.md,
  },
  successText: {
    color: PharmacistTheme.colors.success,
  },
  didContainer: {
    backgroundColor: PharmacistTheme.colors.surface,
    padding: PharmacistTheme.spacing.md,
    borderRadius: 8,
    marginBottom: PharmacistTheme.spacing.lg,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  label: {
    fontWeight: '600',
    marginBottom: PharmacistTheme.spacing.sm,
    color: PharmacistTheme.colors.text,
  },
  didText: {
    fontSize: 12,
    fontFamily: 'monospace',
    backgroundColor: '#F1F5F9',
    padding: 8,
    borderRadius: 4,
    color: PharmacistTheme.colors.text,
  },
  loader: {
    marginTop: 20,
  },
});
