import React from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TextInputProps,
} from 'react-native';
import { PatientTheme } from '@/components/theme/PatientTheme';

/**
 * Props for the ThemedInput component
 * @interface ThemedInputProps
 * @extends TextInputProps
 */
export interface ThemedInputProps extends TextInputProps {
  /** Label displayed above the input */
  label?: React.ReactNode;
  /** Helper text displayed below the input */
  helperText?: string;
  /** Error message displayed below the input (overrides helperText) */
  error?: string;
  /** Icon name to display on the left side (placeholder for future icon library) */
  icon?: string;
  /** Validation state with validity flag and message */
  validation?: {
    isValid: boolean;
    message: string;
  };
}

/**
 * ThemedInput - A text input component with validation, icons, and helper text.
 * 
 * Provides consistent input styling across roles with support for:
 * - Real-time validation states (valid/invalid)
 * - Icon prefixes for visual context
 * - Helper text and error messages
 * - Border color changes based on state
 * - Checkmark indicator when valid
 * 
 * @param {React.ReactNode} [label] - Input field label displayed above the input
 * @param {string} [helperText] - Helper text displayed below the input
 * @param {string} [error] - Error message displayed below the input (overrides helperText)
 * @param {string} [icon] - Icon name to display (mail, lock, user, search, info, check, alert)
 * @param {Object} [validation] - Validation state with validity flag and message
 * @param {boolean} [validation.isValid] - Whether the input is valid
 * @param {string} [validation.message] - Validation message to display
 * @param {StyleProp<TextStyle>} [style] - Additional styles to apply to the TextInput
 * @returns {React.ReactElement} The themed input component
 * 
 * @example
 * ```tsx
 * <ThemedInput
 *   label="Email"
 *   placeholder="Enter your email"
 *   value={email}
 *   onChangeText={setEmail}
 *   icon="mail"
 *   validation={{ isValid: true, message: 'Email looks good' }}
 * />
 * 
 * <ThemedInput
 *   label="Password"
 *   placeholder="Enter password"
 *   secureTextEntry
 *   error="Password is required"
 *   value={password}
 *   onChangeText={setPassword}
 * />
 * ```
 */
export function ThemedInput({
  label,
  helperText,
  error,
  icon,
  validation,
  style,
  ...textInputProps
}: ThemedInputProps): React.ReactElement {
  const theme = PatientTheme;

  /**
   * Determine border color based on state priority:
   * 1. Error state (highest priority)
   * 2. Validation invalid state
   * 3. Validation valid state
   * 4. Default border color
   */
  const getBorderColor = (): string => {
    if (error) return theme.colors.error;
    if (validation?.isValid === false) return theme.colors.error;
    if (validation?.isValid === true) return theme.colors.success;
    return theme.colors.border;
  };

  /**
   * Render simple text-based icon (placeholder for icon library)
   */
  const renderIcon = (): React.ReactNode => {
    if (!icon) return null;
    
    return (
      <View style={styles.iconContainer}>
        <Text style={[styles.icon, { color: theme.colors.textSecondary }]}>
          {icon === 'mail' && '✉'}
          {icon === 'lock' && '🔒'}
          {icon === 'user' && '👤'}
          {icon === 'search' && '🔍'}
          {icon === 'info' && 'ℹ'}
          {icon === 'check' && '✓'}
          {icon === 'alert' && '⚠'}
          {!['mail', 'lock', 'user', 'search', 'info', 'check', 'alert'].includes(icon) && '•'}
        </Text>
      </View>
    );
  };

  /**
   * Render validation checkmark indicator
   */
  const renderValidationIndicator = (): React.ReactNode => {
    if (!validation?.isValid) return null;
    
    return (
      <View style={styles.validationContainer}>
        <Text style={[styles.checkmark, { color: theme.colors.success }]}>✓</Text>
      </View>
    );
  };

  /**
   * Determine text to display below input
   */
  const getHelperText = (): string | undefined => {
    if (error) return error;
    if (validation?.isValid === false) return validation.message;
    if (validation?.isValid === true) return validation.message;
    return helperText;
  };

  /**
   * Determine text color for helper/error message
   */
  const getHelperTextColor = (): string => {
    if (error) return theme.colors.error;
    if (validation?.isValid === false) return theme.colors.error;
    if (validation?.isValid === true) return theme.colors.success;
    return theme.colors.textSecondary;
  };

  const helperTextToShow = getHelperText();

  return (
    <View style={styles.container}>
      {label && (
        <Text style={[styles.label, { color: theme.colors.text }]}>
          {label}
        </Text>
      )}
      
      <View
        style={[
          styles.inputContainer,
          {
            borderColor: getBorderColor(),
            backgroundColor: theme.colors.surface,
          },
        ]}
      >
        {renderIcon()}
        
        <TextInput
          style={[
            styles.input,
            {
              color: theme.colors.text,
              paddingLeft: icon ? 0 : theme.spacing.md,
            },
            style,
          ]}
          placeholderTextColor={theme.colors.textSecondary}
          {...textInputProps}
        />
        
        {renderValidationIndicator()}
      </View>
      
      {helperTextToShow && (
        <Text style={[styles.helperText, { color: getHelperTextColor() }]}>
          {helperTextToShow}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
    width: '100%',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 8,
    minHeight: 48,
  },
  iconContainer: {
    paddingHorizontal: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    fontSize: 18,
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
    paddingRight: 12,
  },
  validationContainer: {
    paddingHorizontal: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  helperText: {
    fontSize: 12,
    marginTop: 4,
    marginLeft: 4,
  },
});

export default ThemedInput;
