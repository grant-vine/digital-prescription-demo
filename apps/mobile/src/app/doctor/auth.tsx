import { useState, useEffect, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuthRequest } from 'expo-auth-session';
import { api } from '../../services/api';
import { DoctorTheme } from '../../components/theme/DoctorTheme';


const ThemedText = ({ style, type = 'body', children, ...props }: any) => {
  const baseStyle = {
    color: DoctorTheme.colors.text,
    ...DoctorTheme.typography[type as keyof typeof DoctorTheme.typography],
  };
  return <Text style={[baseStyle, style]} {...props}>{children}</Text>;
};

const ThemedInput = ({ style, error, ...props }: any) => {
  return (
    <View style={{ marginBottom: DoctorTheme.spacing.md, width: '100%' }}>
      <TextInput
        style={[
          styles.input,
          error && styles.inputError,
          style,
        ]}
        placeholderTextColor={DoctorTheme.colors.textSecondary}
        {...props}
      />
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

const ThemedButton = ({ title, onPress, variant = 'primary', disabled, loading, style, textStyle }: any) => {
  const backgroundColor = variant === 'primary' ? DoctorTheme.colors.primary : 'transparent';
  const textColor = variant === 'primary' ? '#ffffff' : DoctorTheme.colors.primary;
  const borderColor = variant === 'outline' ? DoctorTheme.colors.border : 'transparent';

  const finalStyle = StyleSheet.flatten([
    styles.button,
    { backgroundColor, borderColor, borderWidth: variant === 'outline' ? 1 : 0 },
    disabled && styles.buttonDisabled,
    style
  ]);

  const finalTextStyle = StyleSheet.flatten([
    styles.buttonText,
    { color: textColor },
    textStyle,
    (disabled || loading) && { opacity: 0.6 }
  ]);

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={finalStyle}
      accessibilityState={{ disabled: disabled || loading }}
    >
      {loading ? (
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <ActivityIndicator color={textColor} style={{ marginRight: 8 }} />
          <Text style={finalTextStyle}>
            {title}
          </Text>
        </View>
      ) : (
        <Text 
          style={finalTextStyle}
          accessibilityState={{ disabled: disabled || loading }}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
};


export default function DoctorAuthScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_request, _response, promptAsync] = useAuthRequest(
    {
      clientId: 'mock-client-id',
      scopes: ['openid', 'profile', 'email'],
      redirectUri: 'myapp://oauth-callback',
    },
    { authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth' }
  );

  const checkAuth = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (token) {
        router.replace('/doctor/dashboard');
      }
    } catch (err) {
      // Silent failure - user will see login screen
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const validateEmail = (emailStr: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(emailStr);
  };

  const handleLogin = async () => {
    setError(null);
    setEmailError(null);

    // Validate email format if email has a value
    if (email && !validateEmail(email)) {
      setEmailError('Invalid email format');
      return;
    }

    // Check for empty fields
    if (!email || !password) {
      setError('Required fields missing');
      return;
    }

    setLoading(true);

    try {
      const response = await api.login(email, password);
      
      if (response?.access_token) {
        await AsyncStorage.setItem('access_token', response.access_token);
      }
      if (response?.refresh_token) {
        await AsyncStorage.setItem('refresh_token', response.refresh_token);
      }
      
      router.replace('/doctor/dashboard');
    } catch (err: any) {
      console.log('Login error:', err);
      let errorMessage = 'Something went wrong';
      
      if (err.message === 'Network Error') {
        errorMessage = 'Network error. Please check your connection.';
      } else if (err.response) {
        if (err.response.status === 401) {
          errorMessage = 'Invalid credentials. Please check your email and password.';
        } else if (err.response.status === 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (err.response.data?.detail) {
          errorMessage = err.response.data.detail;
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = !!(email && password && validateEmail(email));

  return (
    <SafeAreaView style={styles.container} testID="doctor-auth-screen">
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
              <ThemedText type="body" style={styles.backButtonText}>← Back</ThemedText>
            </TouchableOpacity>
          </View>

          <View style={styles.content}>
            <View style={styles.logoContainer}>
              <View style={styles.logoPlaceholder}>
                <ThemedText style={styles.logoText}>Rx</ThemedText>
              </View>
              <ThemedText type="h1" style={styles.title}>Doctor Portal</ThemedText>
              <ThemedText type="body" style={styles.subtitle}>Manage your prescriptions</ThemedText>
            </View>

            <View style={styles.form}>
              <ThemedInput
                placeholder="Email or Username"
                value={email}
                onChangeText={(text: string) => {
                  setEmail(text);
                  if (emailError) setEmailError(null);
                  if (error) setError(null);
                }}
                autoCapitalize="none"
                keyboardType="email-address"
                error={emailError}
              />

              <ThemedInput
                placeholder="Password"
                value={password}
                onChangeText={(text: string) => {
                  setPassword(text);
                  if (error) setError(null);
                }}
                secureTextEntry
              />

              {error && (
                <View style={styles.errorContainer}>
                  <ThemedText style={styles.errorMessage}>{error}</ThemedText>
                </View>
              )}

              <ThemedButton
                title={loading ? "Signing in..." : "Login"}
                onPress={handleLogin}
                disabled={loading}
                loading={loading}
                style={[styles.loginButton, (!isFormValid || loading) && { opacity: 0.5 }]}
                textStyle={(!isFormValid || loading) ? { opacity: 0.5 } : undefined}
                accessibilityState={{ disabled: !isFormValid || loading }}
              />

              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <ThemedText style={styles.dividerText}>OR</ThemedText>
                <View style={styles.dividerLine} />
              </View>

              <ThemedButton
                title="Continue with Google"
                variant="outline"
                onPress={() => promptAsync && promptAsync()}
                style={styles.oauthButton}
                textStyle={{ color: DoctorTheme.colors.text }}
              />

              <ThemedButton
                title="Continue with Microsoft"
                variant="outline"
                onPress={() => {}}
                style={styles.oauthButton}
                textStyle={{ color: DoctorTheme.colors.text }}
              />
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: DoctorTheme.colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: DoctorTheme.spacing.lg,
  },
  header: {
    marginBottom: DoctorTheme.spacing.lg,
  },
  backButton: {
    padding: DoctorTheme.spacing.xs,
  },
  backButtonText: {
    color: DoctorTheme.colors.primary,
    fontWeight: '600',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: DoctorTheme.spacing.xl,
  },
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 20,
    backgroundColor: DoctorTheme.colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: DoctorTheme.spacing.md,
    shadowColor: DoctorTheme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  logoText: {
    color: '#ffffff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  title: {
    color: DoctorTheme.colors.text,
    textAlign: 'center',
    marginBottom: DoctorTheme.spacing.xs,
  },
  subtitle: {
    color: DoctorTheme.colors.textSecondary,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  input: {
    backgroundColor: DoctorTheme.colors.surface,
    borderWidth: 1,
    borderColor: DoctorTheme.colors.border,
    borderRadius: 12,
    padding: DoctorTheme.spacing.md,
    fontSize: 16,
    color: DoctorTheme.colors.text,
  },
  inputError: {
    borderColor: DoctorTheme.colors.error,
  },
  errorText: {
    color: DoctorTheme.colors.error,
    fontSize: 12,
    marginTop: 4,
    marginLeft: 4,
  },
  errorContainer: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fee2e2',
    borderRadius: 8,
    padding: DoctorTheme.spacing.md,
    marginBottom: DoctorTheme.spacing.md,
  },
  errorMessage: {
    color: DoctorTheme.colors.error,
    textAlign: 'center',
    fontSize: 14,
  },
  button: {
    height: 56,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: DoctorTheme.spacing.md,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  loginButton: {
    marginTop: DoctorTheme.spacing.xs,
    shadowColor: DoctorTheme.colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 3,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: DoctorTheme.spacing.lg,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: DoctorTheme.colors.border,
  },
  dividerText: {
    marginHorizontal: DoctorTheme.spacing.md,
    color: DoctorTheme.colors.textSecondary,
    fontSize: 14,
  },
  oauthButton: {
    marginBottom: DoctorTheme.spacing.md,
    borderColor: DoctorTheme.colors.border,
    backgroundColor: DoctorTheme.colors.surface,
  },
});
