import React, { useState, useRef } from 'react';
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
import { PatientTheme } from '../../components/theme/PatientTheme';
import { CardContainer } from '../../components/CardContainer';
import { ThemedInput } from '../../components/ThemedInput';
import { StepIndicator, Step as StepType } from '../../components/StepIndicator';
import { DemoLoginButtons, DemoCredentials } from '../../components/DemoLoginButtons';

type Step = 'WELCOME' | 'WALLET' | 'LOGIN';

const steps: StepType[] = [
  { id: 'WELCOME', label: 'Welcome', icon: '👋' },
  { id: 'WALLET', label: 'Create Wallet', icon: '👛' },
  { id: 'LOGIN', label: 'Login', icon: '🔐' },
];

/**
 * Welcome View Component
 * First step - introduces the user to the digital wallet concept
 */
function WelcomeView({
  onCreateWallet,
  onExistingWallet,
}: {
  onCreateWallet: () => void;
  onExistingWallet: () => void;
}): React.ReactElement {
  const theme = PatientTheme;

  return (
    <View style={stepStyles.container}>
      <View style={stepStyles.iconContainer}>
        <Text style={stepStyles.icon}>👤</Text>
      </View>
      
      <Text style={[stepStyles.title, { color: theme.colors.text }]}>
        Welcome to Your Digital Wallet
      </Text>
      
      <Text style={[stepStyles.description, { color: theme.colors.textSecondary }]}>
        Store and manage your prescriptions securely. Your digital wallet gives you complete control over your health records.
      </Text>

      <View style={stepStyles.benefitsContainer}>
        <View style={stepStyles.benefitItem}>
          <Text style={stepStyles.benefitIcon}>🔒</Text>
          <Text style={[stepStyles.benefitText, { color: theme.colors.text }]}>
            Secure digital prescriptions
          </Text>
        </View>
        <View style={stepStyles.benefitItem}>
          <Text style={stepStyles.benefitIcon}>📱</Text>
          <Text style={[stepStyles.benefitText, { color: theme.colors.text }]}>
            Access anywhere, anytime
          </Text>
        </View>
        <View style={stepStyles.benefitItem}>
          <Text style={stepStyles.benefitIcon}>✓</Text>
          <Text style={[stepStyles.benefitText, { color: theme.colors.text }]}>
            Easy pharmacy verification
          </Text>
        </View>
      </View>

      <TouchableOpacity
        style={[stepStyles.primaryButton, { backgroundColor: theme.colors.primary }]}
        onPress={onCreateWallet}
        accessibilityRole="button"
        accessibilityLabel="Create new wallet"
      >
        <Text style={stepStyles.primaryButtonText}>Create New Wallet</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[stepStyles.secondaryButton, { borderColor: theme.colors.border }]}
        onPress={onExistingWallet}
        accessibilityRole="button"
        accessibilityLabel="I already have a wallet"
      >
        <Text style={[stepStyles.secondaryButtonText, { color: theme.colors.primary }]}>
          I Already Have a Wallet
        </Text>
      </TouchableOpacity>
    </View>
  );
}

/**
 * Wallet Creation View Component
 * Second step - creates wallet and DID with loading states
 */
function WalletCreationView({
  walletId,
  did,
  loading,
  error,
  onContinue,
}: {
  walletId: string | null;
  did: string | null;
  loading: boolean;
  error: string | null;
  onContinue: () => void;
}): React.ReactElement {
  const theme = PatientTheme;

  return (
    <View style={stepStyles.container}>
      {loading && !walletId && (
        <View style={stepStyles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[stepStyles.loadingText, { color: theme.colors.text }]} testID="wallet-creating-indicator">
            Creating your secure wallet...
          </Text>
          <Text style={[stepStyles.loadingSubtext, { color: theme.colors.textSecondary }]}>
            This may take a moment
          </Text>
        </View>
      )}

      {error && (
        <View
          style={[stepStyles.errorBanner, { backgroundColor: `${theme.colors.error}15` }]}
          testID="wallet-error-message"
        >
          <Text style={stepStyles.errorIcon}>⚠️</Text>
          <Text style={[stepStyles.errorText, { color: theme.colors.error }]}>{error}</Text>
        </View>
      )}

      {walletId && (
        <View style={stepStyles.successContainer} testID="wallet-success-message">
          <View style={[stepStyles.successIconContainer, { backgroundColor: `${theme.colors.success}20` }]}>
            <Text style={stepStyles.successIcon}>✓</Text>
          </View>
          
          <Text style={[stepStyles.successTitle, { color: theme.colors.success }]}>
            Wallet Created Successfully!
          </Text>
          
          <View style={[stepStyles.infoCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
            <Text style={[stepStyles.infoLabel, { color: theme.colors.textSecondary }]}>
              Wallet ID
            </Text>
            <Text style={[stepStyles.infoValue, { color: theme.colors.text }]} testID="wallet-id-display">
              {walletId}
            </Text>
          </View>

          {did && (
            <View style={[stepStyles.infoCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]} testID="patient-did-display">
              <Text style={[stepStyles.infoLabel, { color: theme.colors.textSecondary }]}>
                Your Digital Identifier (DID)
              </Text>
              <Text style={[stepStyles.didText, { color: theme.colors.text, backgroundColor: `${theme.colors.primary}08` }]}>
                {did}
              </Text>
            </View>
          )}

          <TouchableOpacity
            style={[stepStyles.primaryButton, { backgroundColor: theme.colors.primary, marginTop: 24 }]}
            onPress={onContinue}
            accessibilityRole="button"
            accessibilityLabel="Continue to login"
          >
            <Text style={stepStyles.primaryButtonText}>Continue to Login</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

/**
 * Login Form View Component
 * Third step - email/password login form
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
  const theme = PatientTheme;
  const [showPassword, setShowPassword] = useState(false);

  return (
    <View style={stepStyles.container}>
      <Text style={[stepStyles.loginTitle, { color: theme.colors.text }]}>
        Sign In to Your Wallet
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
        placeholder="john.smith@example.com"
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
        disabled={loading}
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
 * Patient Authentication Screen
 * 3-step flow: Welcome → Wallet Creation → Login
 */
export default function PatientAuthScreen(): React.ReactElement {
  const theme = PatientTheme;
  const [step, setStep] = useState<Step>('WELCOME');
  const [walletId, setWalletId] = useState<string | null>(null);
  const [did, setDid] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Animation values
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const translateAnim = useRef(new Animated.Value(0)).current;

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
   * Handle wallet creation
   */
  const handleCreateWallet = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      animateStepTransition('forward');
      setStep('WALLET');

      const walletResponse = await api.createWallet();
      setWalletId(walletResponse.wallet_id);

      const didResponse = await api.setupPatientDID(walletResponse.wallet_id);
      setDid(didResponse.did);

      await AsyncStorage.setItem('patient_did', didResponse.did);
    } catch (err: unknown) {
      console.error('Wallet creation error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to create wallet';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle "I already have a wallet" - skip to login
   */
  const handleExistingWallet = (): void => {
    animateStepTransition('forward');
    setStep('LOGIN');
  };

  /**
   * Continue from wallet creation to login
   */
  const handleContinueToLogin = (): void => {
    animateStepTransition('forward');
    setStep('LOGIN');
  };

  /**
   * Handle login form submission
   */
  const handleLogin = async (): Promise<void> => {
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const authResponse = await api.authenticatePatient(email, password);
      await AsyncStorage.setItem('auth_token', authResponse.token);

      router.replace('/patient/wallet');
    } catch (err: unknown) {
      console.error('Login error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Authentication failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle demo credentials selection
   */
  const handleDemoSelect = (credentials: DemoCredentials): void => {
    setEmail(credentials.email);
    setPassword(credentials.password);
    
    // Auto-navigate to login step if not already there
    if (step !== 'LOGIN') {
      animateStepTransition('forward');
      setStep('LOGIN');
    }
  };

  /**
   * Render the appropriate step content
   */
  const renderStepContent = (): React.ReactElement => {
    switch (step) {
      case 'WELCOME':
        return (
          <WelcomeView
            onCreateWallet={handleCreateWallet}
            onExistingWallet={handleExistingWallet}
          />
        );
      case 'WALLET':
        return (
          <WalletCreationView
            walletId={walletId}
            did={did}
            loading={loading}
            error={error}
            onContinue={handleContinueToLogin}
          />
        );
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
      default:
        return (
          <WelcomeView
            onCreateWallet={handleCreateWallet}
            onExistingWallet={handleExistingWallet}
          />
        );
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]} testID="patient-auth-screen">
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
              <Text style={styles.headerIcon}>👤</Text>
              <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
                Patient Wallet
              </Text>
              <Text style={[styles.headerSubtitle, { color: theme.colors.textSecondary }]}>
                Your secure prescription management
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
              currentRole="patient"
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
  // Welcome View Styles
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
  benefitsContainer: {
    marginBottom: 32,
    gap: 12,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  benefitIcon: {
    fontSize: 20,
    width: 32,
    textAlign: 'center',
  },
  benefitText: {
    fontSize: 14,
    flex: 1,
  },
  // Button Styles
  primaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    backgroundColor: 'transparent',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  // Wallet Creation Styles
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
  successIcon: {
    fontSize: 32,
    color: '#FFFFFF',
    fontWeight: 'bold',
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
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  didText: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    padding: 8,
    borderRadius: 4,
    marginTop: 4,
  },
  // Login View Styles
  loginTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 24,
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
});
