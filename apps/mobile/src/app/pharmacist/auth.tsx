import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  Animated,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../../services/api';
import { PharmacistTheme } from '../../components/theme/PharmacistTheme';
import { CardContainer } from '../../components/CardContainer';
import { ThemedInput } from '../../components/ThemedInput';
import { StepIndicator, Step as StepType } from '../../components/StepIndicator';
import { DemoLoginButtons, DemoCredentials } from '../../components/DemoLoginButtons';
import { InfoTooltip } from '../../components/InfoTooltip';

type Step = 'LOGIN' | 'PROFILE' | 'SAPC' | 'DID';

const steps: StepType[] = [
  { id: 'LOGIN', label: 'Login', icon: '🔐' },
  { id: 'PROFILE', label: 'Profile', icon: '👤' },
  { id: 'SAPC', label: 'SAPC', icon: '🛡️' },
  { id: 'DID', label: 'Identity', icon: '🔑' },
];

/**
 * SAPC Help Text for InfoTooltip
 */
const SAPC_HELP_TEXT = `South African Pharmacy Council (SAPC) Registration

The SAPC number is your official registration identifier issued by the South African Pharmacy Council. It verifies you are a licensed pharmacist authorized to dispense medications in South Africa.

Why it's required:
• Legal requirement for all practicing pharmacists
• Ensures only qualified professionals dispense
• Required for digital prescription verification
• Part of compliance audit trail

Format: SAPC followed by 6 digits
Example: SAPC123456

Forgot your number? Contact SAPC at www.sapc.za.org`;

/**
 * Login Form View Component
 * First step - email/password login
 */
function LoginFormView({
  email,
  password,
  loading,
  error,
  onEmailChange,
  onPasswordChange,
  onLogin,
}: {
  email: string;
  password: string;
  loading: boolean;
  error: string | null;
  onEmailChange: (email: string) => void;
  onPasswordChange: (password: string) => void;
  onLogin: () => void;
}): React.ReactElement {
  const theme = PharmacistTheme;
  const [showPassword, setShowPassword] = useState(false);

  return (
    <View style={stepStyles.container}>
      <Text style={[stepStyles.loginTitle, { color: theme.colors.text }]}>
        Sign In
      </Text>

      <Text style={[stepStyles.loginSubtitle, { color: theme.colors.textSecondary }]} testID="pharmacist-login-instructions">
        Welcome to the Pharmacy Management System. Sign in with your credentials to set up your pharmacy profile and digital identity.
      </Text>

      {error && (
        <View
          style={[stepStyles.errorBanner, { backgroundColor: `${theme.colors.error}15` }]}
          testID="login-error-message"
        >
          <Text style={stepStyles.errorIcon}>⚠️</Text>
          <Text style={[stepStyles.errorText, { color: theme.colors.error }]}>{error}</Text>
        </View>
      )}

      <ThemedInput
        label="Email Address"
        placeholder="lisa.chen@pharmacy.co.za"
        value={email}
        onChangeText={onEmailChange}
        icon="mail"
        autoCapitalize="none"
        keyboardType="email-address"
        editable={!loading}
        testID="email-input"
      />

      <View style={stepStyles.passwordContainer}>
        <ThemedInput
          label="Password"
          placeholder="Enter your password"
          value={password}
          onChangeText={onPasswordChange}
          icon="lock"
          secureTextEntry={!showPassword}
          editable={!loading}
          testID="password-input"
        />
        <TouchableOpacity
          style={stepStyles.visibilityToggle}
          onPress={() => setShowPassword(!showPassword)}
          accessibilityRole="button"
          accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
        >
          <Text style={[stepStyles.visibilityIcon, { color: theme.colors.textSecondary }]}>
            {showPassword ? '🙈' : '👁️'}
          </Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[
          stepStyles.primaryButton,
          { backgroundColor: theme.colors.primary },
          loading && { opacity: 0.7 },
        ]}
        onPress={onLogin}
        disabled={loading || !email || !password}
        accessibilityRole="button"
        accessibilityLabel="Sign in"
        accessibilityState={{ disabled: loading }}
        testID="login-button"
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" size="small" />
        ) : (
          <Text style={stepStyles.primaryButtonText}>Sign In</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

/**
 * Profile Setup View Component
 * Second step - pharmacy name and details
 */
function ProfileSetupView({
  pharmacyName,
  pharmacyRegNumber,
  loading,
  error,
  onPharmacyNameChange,
  onPharmacyRegChange,
  onContinue,
}: {
  pharmacyName: string;
  pharmacyRegNumber: string;
  loading: boolean;
  error: string | null;
  onPharmacyNameChange: (name: string) => void;
  onPharmacyRegChange: (reg: string) => void;
  onContinue: () => void;
}): React.ReactElement {
  const theme = PharmacistTheme;

  return (
    <View style={stepStyles.container}>
      <View style={stepStyles.iconContainer}>
        <Text style={stepStyles.icon}>🏥</Text>
      </View>

      <Text style={[stepStyles.title, { color: theme.colors.text }]}>
        Setup Your Pharmacy Profile
      </Text>

      <Text style={[stepStyles.description, { color: theme.colors.textSecondary }]}>
        Enter your pharmacy details to complete your profile setup.
      </Text>

      {error && (
        <View
          style={[stepStyles.errorBanner, { backgroundColor: `${theme.colors.error}15` }]}
          testID="profile-error-message"
        >
          <Text style={stepStyles.errorIcon}>⚠️</Text>
          <Text style={[stepStyles.errorText, { color: theme.colors.error }]}>{error}</Text>
        </View>
      )}

      <ThemedInput
        label="Pharmacy Name"
        placeholder="e.g., MediCare Pharmacy"
        value={pharmacyName}
        onChangeText={onPharmacyNameChange}
        icon="info"
        editable={!loading}
        testID="pharmacy-name-input"
      />

      <ThemedInput
        label="Pharmacy Registration Number (Optional)"
        placeholder="e.g., PHARM-2024-001"
        value={pharmacyRegNumber}
        onChangeText={onPharmacyRegChange}
        icon="info"
        editable={!loading}
      />

      <View style={[stepStyles.infoBox, { backgroundColor: `${theme.colors.primary}10`, borderColor: theme.colors.border }]}>
        <Text style={[stepStyles.infoBoxTitle, { color: theme.colors.primary }]}>ℹ️ Profile Information</Text>
        <Text style={[stepStyles.infoBoxText, { color: theme.colors.text }]}>
          Your pharmacy profile will be linked to your digital identity for secure prescription verification.
        </Text>
      </View>

      <TouchableOpacity
        style={[
          stepStyles.primaryButton,
          { backgroundColor: theme.colors.primary },
          loading && { opacity: 0.7 },
        ]}
        onPress={onContinue}
        disabled={loading || !pharmacyName.trim()}
        accessibilityRole="button"
        accessibilityLabel="Continue to SAPC validation"
        testID="continue-sapc-button"
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" size="small" />
        ) : (
          <Text style={stepStyles.primaryButtonText}>Continue</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

/**
 * SAPC Validation View Component
 * Third step - SAPC number with validation and InfoTooltip
 */
function SAPCValidationView({
  sapcNumber,
  sapcValidated,
  sapcError,
  loading,
  onSAPCChange,
  onContinue,
}: {
  sapcNumber: string;
  sapcValidated: boolean;
  sapcError: string | null;
  loading: boolean;
  onSAPCChange: (value: string) => void;
  onContinue: () => void;
}): React.ReactElement {
  const theme = PharmacistTheme;

  return (
    <View style={stepStyles.container}>
      <View style={stepStyles.iconContainer}>
        <Text style={stepStyles.icon}>🛡️</Text>
      </View>

      <Text style={[stepStyles.title, { color: theme.colors.text }]}>
        SAPC Registration
      </Text>

      <Text style={[stepStyles.description, { color: theme.colors.textSecondary }]}>
        Enter your South African Pharmacy Council registration number to verify your credentials.
      </Text>

      {sapcError && (
        <View
          style={[stepStyles.errorBanner, { backgroundColor: `${theme.colors.error}15` }]}
          testID="sapc-error-message"
        >
          <Text style={stepStyles.errorIcon}>⚠️</Text>
          <Text style={[stepStyles.errorText, { color: theme.colors.error }]}>{sapcError}</Text>
        </View>
      )}

      {sapcValidated && !sapcError && (
        <View
          style={[stepStyles.successBanner, { backgroundColor: `${theme.colors.success}15` }]}
          testID="sapc-success-message"
        >
          <Text style={stepStyles.successIcon}>✓</Text>
          <Text style={[stepStyles.successText, { color: theme.colors.success }]}>
            SAPC registration verified and registered
          </Text>
        </View>
      )}

      <View style={stepStyles.labelRow}>
        <Text style={[stepStyles.labelText, { color: theme.colors.text }]}>
          SAPC Number
        </Text>
        <InfoTooltip
          title="What is SAPC?"
          content={SAPC_HELP_TEXT}
          icon="help"
        />
      </View>

      <ThemedInput
        placeholder="SAPC123456"
        value={sapcNumber}
        onChangeText={onSAPCChange}
        icon="info"
        editable={!loading}
        testID="sapc-input"
        validation={sapcValidated ? { isValid: true, message: 'Valid SAPC format' } : undefined}
      />

      <Text style={[stepStyles.formatHint, { color: theme.colors.textSecondary }]}>
        Format: SAPC followed by 6 digits (e.g., SAPC123456)
      </Text>

      <TouchableOpacity
        style={[
          stepStyles.primaryButton,
          { backgroundColor: theme.colors.primary },
          (!sapcValidated || loading) && { opacity: 0.7 },
        ]}
        onPress={onContinue}
        disabled={!sapcValidated || loading}
        accessibilityRole="button"
        accessibilityLabel="Continue to identity creation"
        testID="continue-did-button"
      >
        {loading ? (
          <ActivityIndicator color="#FFFFFF" size="small" />
        ) : (
          <Text style={stepStyles.primaryButtonText}>Continue</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

/**
 * DID Creation View Component
 * Fourth step - create digital identity
 */
function DIDCreationView({
  did,
  loading,
  error,
  onCreateDID,
  onComplete,
}: {
  did: string | null;
  loading: boolean;
  error: string | null;
  onCreateDID: () => void;
  onComplete: () => void;
}): React.ReactElement {
  const theme = PharmacistTheme;

  return (
    <View style={stepStyles.container}>
      {!did && !loading && (
        <>
          <View style={stepStyles.iconContainer}>
            <Text style={stepStyles.icon}>🔑</Text>
          </View>

          <Text style={[stepStyles.title, { color: theme.colors.text }]}>
            Create Your Digital Identity
          </Text>

          <Text style={[stepStyles.description, { color: theme.colors.textSecondary }]}>
            Create a secure digital identity (DID) to verify prescriptions and participate in the digital prescription network.
          </Text>

          <View style={[stepStyles.infoBox, { backgroundColor: `${theme.colors.primary}10`, borderColor: theme.colors.border }]}>
            <Text style={[stepStyles.infoBoxTitle, { color: theme.colors.primary }]}>🔐 About Digital Identity</Text>
            <Text style={[stepStyles.infoBoxText, { color: theme.colors.text }]}>
              Your Decentralized Identifier (DID) is a unique, cryptographically secure identifier that allows you to verify and dispense digital prescriptions while maintaining patient privacy.
            </Text>
          </View>

          {error && (
            <View
              style={[stepStyles.errorBanner, { backgroundColor: `${theme.colors.error}15` }]}
              testID="did-error-message"
            >
              <Text style={stepStyles.errorIcon}>⚠️</Text>
              <Text style={[stepStyles.errorText, { color: theme.colors.error }]}>{error}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[
              stepStyles.primaryButton,
              { backgroundColor: theme.colors.primary },
              loading && { opacity: 0.7 },
            ]}
            onPress={onCreateDID}
            disabled={loading}
            accessibilityRole="button"
            accessibilityLabel="Create digital identity"
            testID="generate-did-button"
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={stepStyles.primaryButtonText}>Create Digital Identity</Text>
            )}
          </TouchableOpacity>
        </>
      )}

      {loading && !did && (
        <View style={stepStyles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[stepStyles.loadingText, { color: theme.colors.text }]}>
            Creating your digital identity...
          </Text>
          <Text style={[stepStyles.loadingSubtext, { color: theme.colors.textSecondary }]}>
            This may take a moment
          </Text>
        </View>
      )}

      {did && (
        <View style={stepStyles.successContainer}>
          <View style={[stepStyles.successIconContainer, { backgroundColor: `${theme.colors.success}20` }]}>
            <Text style={stepStyles.successIcon}>✓</Text>
          </View>

          <Text style={[stepStyles.successTitle, { color: theme.colors.success }]}>
            Identity Created Successfully!
          </Text>

          <View style={[stepStyles.infoCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
            <Text style={[stepStyles.infoLabel, { color: theme.colors.textSecondary }]}>
              Your Digital Identifier (DID)
            </Text>
            <Text
              style={[stepStyles.didText, { color: theme.colors.text, backgroundColor: `${theme.colors.primary}08` }]}
              testID="pharmacist-did-display"
            >
              {did}
            </Text>
          </View>

          <TouchableOpacity
            style={[stepStyles.primaryButton, { backgroundColor: theme.colors.primary, marginTop: 24 }]}
            onPress={onComplete}
            accessibilityRole="button"
            accessibilityLabel="Continue to dashboard"
          >
            <Text style={stepStyles.primaryButtonText}>Continue to Dashboard</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

/**
 * Pharmacist Authentication Screen
 * 4-step flow: Login → Profile Setup → SAPC Validation → DID Creation
 */
export default function PharmacistAuthScreen(): React.ReactElement {
  const theme = PharmacistTheme;
  const [step, setStep] = useState<Step>('LOGIN');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pharmacistId, setPharmacistId] = useState<string | null>(null);

  // Profile state
  const [pharmacyName, setPharmacyName] = useState('');
  const [pharmacyRegNumber, setPharmacyRegNumber] = useState('');

  // SAPC state
  const [sapcNumber, setSapcNumber] = useState('');
  const [sapcValidated, setSAPCValidated] = useState(false);
  const [sapcError, setSAPCError] = useState<string | null>(null);

  // DID state
  const [did, setDid] = useState<string | null>(null);

  // Animation values
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const translateAnim = useRef(new Animated.Value(0)).current;

  /**
   * Validate SAPC format (SAPC + 6 digits)
   */
  const validateSAPCFormat = useCallback((value: string): boolean => {
    return /^SAPC\d{6}$/.test(value);
  }, []);

  /**
   * Handle SAPC input change with real-time validation
   */
  const handleSAPCChange = useCallback((value: string) => {
    setSapcNumber(value);
    const isValid = validateSAPCFormat(value);
    setSAPCValidated(isValid);
    if (isValid) {
      setSAPCError(null);
    }
  }, [validateSAPCFormat]);

  /**
   * Animate step transitions
   */
  const animateStepTransition = (direction: 'forward' | 'backward'): void => {
    const toValue = direction === 'forward' ? -20 : 20;

    Animated.sequence([
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(translateAnim, {
          toValue: toValue,
          duration: 150,
          useNativeDriver: true,
        }),
      ]),
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(translateAnim, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  };

  /**
   * Handle login
   */
  const handleLogin = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const authResponse = await api.authenticatePharmacist(email, password);
      setPharmacistId(authResponse.pharmacist.id);
      await AsyncStorage.setItem('auth_token', authResponse.token);

      animateStepTransition('forward');
      setStep('PROFILE');
    } catch (err: unknown) {
      console.error('Login error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [email, password]);

  /**
   * Handle profile setup and continue to SAPC
   */
  const handleProfileContinue = useCallback(async () => {
    animateStepTransition('forward');
    setStep('SAPC');
  }, []);

  /**
   * Handle SAPC validation and continue to DID creation
   */
  const handleSAPCContinue = useCallback(async () => {
    if (!sapcValidated) {
      setSAPCError('Please enter a valid SAPC number');
      return;
    }

    try {
      setLoading(true);
      setSAPCError(null);

      // Call API to validate SAPC on the server
      await api.validateSAPC(sapcNumber);

      animateStepTransition('forward');
      setStep('DID');
    } catch (err: unknown) {
      console.error('SAPC validation error:', err);
      const errorMessage = err instanceof Error ? err.message : 'SAPC validation failed';
      setSAPCError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [sapcNumber, sapcValidated]);

  /**
   * Handle DID creation
   */
  const handleCreateDID = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      if (!pharmacistId) {
        setError('Pharmacist ID not available');
        return;
      }

      // Setup pharmacy first
      await api.setupPharmacy({
        pharmacy_name: pharmacyName,
        sapc_number: sapcNumber,
      });

      // Create DID
      const didResponse = await api.createPharmacistDID(pharmacistId);
      setDid(didResponse.did);
      await AsyncStorage.setItem('pharmacist_did', didResponse.did);
    } catch (err: unknown) {
      console.error('DID creation error:', err);
      const errorMessage = err instanceof Error ? err.message : 'DID creation failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [pharmacistId, pharmacyName, sapcNumber]);

  /**
   * Handle completion - navigate to verify screen
   */
  const handleComplete = useCallback(() => {
    router.replace('/pharmacist/verify');
  }, []);

  /**
   * Handle demo credentials selection
   */
  const handleDemoSelect = (credentials: DemoCredentials): void => {
    setEmail(credentials.email);
    setPassword(credentials.password);

    // Auto-navigate to login step if not already there
    if (step !== 'LOGIN') {
      animateStepTransition('backward');
      setStep('LOGIN');
    }
  };

  /**
   * Render the appropriate step content
   */
  const renderStepContent = (): React.ReactElement => {
    switch (step) {
      case 'LOGIN':
        return (
          <LoginFormView
            email={email}
            password={password}
            loading={loading}
            error={error}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onLogin={handleLogin}
          />
        );
      case 'PROFILE':
        return (
          <ProfileSetupView
            pharmacyName={pharmacyName}
            pharmacyRegNumber={pharmacyRegNumber}
            loading={loading}
            error={error}
            onPharmacyNameChange={setPharmacyName}
            onPharmacyRegChange={setPharmacyRegNumber}
            onContinue={handleProfileContinue}
          />
        );
      case 'SAPC':
        return (
          <SAPCValidationView
            sapcNumber={sapcNumber}
            sapcValidated={sapcValidated}
            sapcError={sapcError}
            loading={loading}
            onSAPCChange={handleSAPCChange}
            onContinue={handleSAPCContinue}
          />
        );
      case 'DID':
        return (
          <DIDCreationView
            did={did}
            loading={loading}
            error={error}
            onCreateDID={handleCreateDID}
            onComplete={handleComplete}
          />
        );
      default:
        return (
          <LoginFormView
            email={email}
            password={password}
            loading={loading}
            error={error}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onLogin={handleLogin}
          />
        );
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} testID="pharmacist-auth-screen">
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoidingView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <CardContainer maxWidth={480}>
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.headerIcon}>💊</Text>
              <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
                Pharmacy Onboarding
              </Text>
              <Text style={[styles.headerSubtitle, { color: theme.colors.textSecondary }]}>
                Set up your digital dispensing profile
              </Text>
            </View>

            {/* Step Indicator */}
            <StepIndicator
              steps={steps}
              currentStep={step}
              onStepPress={(stepId) => {
                // Allow navigation to previous steps only
                const currentIndex = steps.findIndex((s) => s.id === step);
                const targetIndex = steps.findIndex((s) => s.id === stepId);
                if (targetIndex < currentIndex) {
                  animateStepTransition('backward');
                  setStep(stepId as Step);
                }
              }}
            />

            {/* Step Content with Animation */}
            <Animated.View
              style={[
                styles.contentWrapper,
                {
                  opacity: fadeAnim,
                  transform: [{ translateX: translateAnim }],
                },
              ]}
            >
              {renderStepContent()}
            </Animated.View>

            {/* Demo Login Buttons */}
            <DemoLoginButtons
              onSelect={handleDemoSelect}
              currentRole="pharmacist"
            />
          </CardContainer>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingVertical: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  headerIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    textAlign: 'center',
  },
  contentWrapper: {
    width: '100%',
  },
});

const stepStyles = StyleSheet.create({
  container: {
    width: '100%',
    paddingVertical: 16,
  },
  iconContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  icon: {
    fontSize: 64,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  description: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  labelText: {
    fontSize: 14,
    fontWeight: '600',
  },
  formatHint: {
    fontSize: 12,
    marginTop: -8,
    marginBottom: 16,
    marginLeft: 4,
  },
  // Login View Styles
  loginTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  loginSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
    paddingHorizontal: 8,
  },
  passwordContainer: {
    position: 'relative',
  },
  visibilityToggle: {
    position: 'absolute',
    right: 12,
    top: 38,
    padding: 8,
  },
  visibilityIcon: {
    fontSize: 20,
  },
  // Info Box Styles
  infoBox: {
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 24,
  },
  infoBoxTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoBoxText: {
    fontSize: 13,
    lineHeight: 20,
  },
  // Button Styles
  primaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  // Error/Success Banner Styles
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  errorIcon: {
    fontSize: 18,
  },
  errorText: {
    fontSize: 14,
    flex: 1,
    lineHeight: 20,
  },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    gap: 8,
  },
  successIcon: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  successText: {
    fontSize: 14,
    flex: 1,
    lineHeight: 20,
  },
  // Loading Styles
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 14,
  },
  // Success Container Styles
  successContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  successIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  infoCard: {
    width: '100%',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 12,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  didText: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    padding: 8,
    borderRadius: 4,
    marginTop: 4,
  },
});
