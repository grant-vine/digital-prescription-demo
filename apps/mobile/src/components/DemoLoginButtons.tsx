import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Constants from 'expo-constants';
import { PatientTheme } from '@/components/theme/PatientTheme';
import { DoctorTheme } from '@/components/theme/DoctorTheme';
import { PharmacistTheme } from '@/components/theme/PharmacistTheme';

/** Role type for demo credentials */
type Role = 'doctor' | 'patient' | 'pharmacist';

/**
 * Demo credentials interface
 * @interface DemoCredentials
 */
export interface DemoCredentials {
  /** Display label for the button */
  label: string;
  /** Email address for login */
  email: string;
  /** Password for login */
  password: string;
  /** User role */
  role: Role;
}

/**
 * Predefined demo credentials for each role
 * @constant DEMO_CREDENTIALS
 */
export const DEMO_CREDENTIALS: Record<string, DemoCredentials> = {
  doctor: {
    label: '👨‍⚕️ Use Demo Doctor',
    email: 'sarah.johnson@hospital.co.za',
    password: 'Demo@2024',
    role: 'doctor',
  },
  patient: {
    label: '👤 Use Demo Patient',
    email: 'john.smith@example.com',
    password: 'Demo@2024',
    role: 'patient',
  },
  pharmacist: {
    label: '💊 Use Demo Pharmacist',
    email: 'lisa.chen@pharmacy.co.za',
    password: 'Demo@2024',
    role: 'pharmacist',
  },
};

/**
 * Props for the DemoLoginButtons component
 * @interface DemoLoginButtonsProps
 */
export interface DemoLoginButtonsProps {
  /** Callback when a demo credential is selected */
  onSelect: (credentials: DemoCredentials) => void;
  /** Currently selected role (for highlighting active state) */
  currentRole?: Role;
}

/**
 * Get theme colors based on role
 */
const getRoleTheme = (role: Role) => {
  switch (role) {
    case 'doctor':
      return DoctorTheme.colors;
    case 'patient':
      return PatientTheme.colors;
    case 'pharmacist':
      return PharmacistTheme.colors;
    default:
      return PatientTheme.colors;
  }
};

/**
 * DemoLoginButtons - A component that displays demo login buttons for each role.
 * 
 * Features:
 * - Warning banner indicating demo mode
 * - Outlined buttons for each role (Doctor, Patient, Pharmacist)
 * - Active state highlighting for current role
 * - Helper text explaining functionality
 * - Only renders when demoMode is enabled in Expo config
 * - Role-specific color theming
 * - Accessible with proper ARIA labels and roles
 * 
 * @param {Function} onSelect - Callback when a demo credential is selected, receives DemoCredentials object
 * @param {'doctor' | 'patient' | 'pharmacist'} [currentRole] - Currently selected role (for highlighting active state)
 * @returns {React.ReactElement | null} The demo buttons component, or null if demo mode is not enabled
 * 
 * @example
 * ```tsx
 * <DemoLoginButtons
 *   onSelect={(creds) => {
 *     setEmail(creds.email);
 *     setPassword(creds.password);
 *     setRole(creds.role);
 *   }}
 *   currentRole="patient"
 * />
 * 
 * // Using with state management
 * function LoginScreen() {
 *   const [email, setEmail] = useState('');
 *   const [password, setPassword] = useState('');
 *   const [role, setRole] = useState<'doctor' | 'patient' | 'pharmacist'>('patient');
 * 
 *   return (
 *     <View>
 *       <DemoLoginButtons
 *         onSelect={(creds) => {
 *           setEmail(creds.email);
 *           setPassword(creds.password);
 *           setRole(creds.role);
 *         }}
 *         currentRole={role}
 *       />
 *       <ThemedInput
 *         label="Email"
 *         value={email}
 *         onChangeText={setEmail}
 *       />
 *     </View>
 *   );
 * }
 * ```
 */
export function DemoLoginButtons({
  onSelect,
  currentRole,
}: DemoLoginButtonsProps): React.ReactElement | null {
  const theme = PatientTheme;

  /**
   * Check if demo mode is enabled in Expo config
   * Returns null if not in demo mode
   */
  const isDemoMode = Constants.expoConfig?.extra?.demoMode;
  if (!isDemoMode) {
    return null;
  }

  return (
    <View style={styles.container}>
      {/* Warning Banner */}
      <View
        style={[
          styles.warningBanner,
          { backgroundColor: `${theme.colors.warning}20` },
        ]}
      >
        <Text style={[styles.warningIcon, { color: theme.colors.warning }]}>
          ⚠️
        </Text>
        <Text style={[styles.warningText, { color: theme.colors.warning }]}>
          DEMO MODE ONLY
        </Text>
      </View>

      {/* Demo Buttons */}
      <View style={styles.buttonsContainer}>
        {(Object.keys(DEMO_CREDENTIALS) as Role[]).map((role) => {
          const credentials = DEMO_CREDENTIALS[role];
          const roleTheme = getRoleTheme(role);
          const isActive = currentRole === role;

          return (
            <TouchableOpacity
              key={role}
              style={[
                styles.button,
                {
                  borderColor: isActive
                    ? roleTheme.primary
                    : theme.colors.border,
                  backgroundColor: isActive
                    ? `${roleTheme.primary}10`
                    : 'transparent',
                },
              ]}
              onPress={() => onSelect(credentials)}
              accessibilityLabel={`Login as ${role}`}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
            >
              <Text
                style={[
                  styles.buttonText,
                  {
                    color: isActive ? roleTheme.primary : theme.colors.text,
                    fontWeight: isActive ? '600' : '400',
                  },
                ]}
              >
                {credentials.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Helper Text */}
      <Text
        style={[styles.helperText, { color: theme.colors.textSecondary }]}
      >
        Click to auto-fill demo credentials
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    marginVertical: 16,
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 12,
    gap: 6,
  },
  warningIcon: {
    fontSize: 16,
  },
  warningText: {
    fontSize: 14,
    fontWeight: '600',
  },
  buttonsContainer: {
    gap: 8,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 14,
  },
  helperText: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 12,
    fontStyle: 'italic',
  },
});

export default DemoLoginButtons;
