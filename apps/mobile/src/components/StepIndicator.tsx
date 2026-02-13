import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { PatientTheme } from '@/components/theme/PatientTheme';

/**
 * Step definition for the step indicator
 * @interface Step
 */
export interface Step {
  /** Unique identifier for the step */
  id: string;
  /** Display label for the step */
  label: string;
  /** Icon symbol to display in the step circle */
  icon: string;
}

/**
 * Props for the StepIndicator component
 * @interface StepIndicatorProps
 */
export interface StepIndicatorProps {
  /** Array of step definitions */
  steps: Step[];
  /** ID of the currently active step */
  currentStep: string;
  /** Optional callback when a step is pressed (enables navigation) */
  onStepPress?: (stepId: string) => void;
}

/**
 * StepIndicator - A horizontal step indicator component showing progress through a multi-step process.
 * 
 * Features:
 * - Horizontal layout with connecting progress bar
 * - Each step displays an icon and label
 * - Active step highlighted with filled circle and bold text
 * - Completed steps show checkmark icon
 * - Inactive steps are grayed out
 * - Tappable steps when onStepPress callback is provided
 * - Accessible with ARIA labels and roles
 * 
 * @param {Step[]} steps - Array of step definitions with id, label, and icon
 * @param {string} currentStep - ID of the currently active step
 * @param {Function} [onStepPress] - Optional callback when a step is pressed, receives stepId (enables navigation)
 * @returns {React.ReactElement} The step indicator component with progress bar
 * 
 * @example
 * ```tsx
 * const steps = [
 *   { id: 'auth', label: 'Login', icon: '🔐' },
 *   { id: 'verify', label: 'Verify', icon: '✓' },
 *   { id: 'complete', label: 'Done', icon: '✓' },
 * ];
 * 
 * <StepIndicator
 *   steps={steps}
 *   currentStep="verify"
 *   onStepPress={(stepId) => {
 *     console.log('Navigate to', stepId);
 *     router.push(`/flow/${stepId}`);
 *   }}
 * />
 * 
 * // Without click handling
 * <StepIndicator
 *   steps={steps}
 *   currentStep="auth"
 * />
 * ```
 */
export function StepIndicator({
  steps,
  currentStep,
  onStepPress,
}: StepIndicatorProps): React.ReactElement {
  const theme = PatientTheme;

  /**
   * Find the index of the current step
   */
  const currentIndex = steps.findIndex((step) => step.id === currentStep);

  /**
   * Determine if a step is completed (before current)
   */
  const isStepCompleted = (index: number): boolean => {
    return index < currentIndex;
  };

  /**
   * Determine if a step is active
   */
  const isStepActive = (index: number): boolean => {
    return index === currentIndex;
  };

  /**
   * Get the icon to display for a step
   * - Completed steps show checkmark
   * - Active/inactive steps show their defined icon
   */
  const getStepIcon = (step: Step, index: number): string => {
    if (isStepCompleted(index)) {
      return '✓';
    }
    return step.icon;
  };

  /**
   * Get background color for step circle
   */
  const getCircleBackground = (index: number): string => {
    if (isStepActive(index)) {
      return theme.colors.primary;
    }
    if (isStepCompleted(index)) {
      return theme.colors.success;
    }
    return theme.colors.surface;
  };

  /**
   * Get border color for step circle
   */
  const getCircleBorderColor = (index: number): string => {
    if (isStepActive(index) || isStepCompleted(index)) {
      return 'transparent';
    }
    return theme.colors.border;
  };

  /**
   * Get text color for step icon
   */
  const getIconColor = (index: number): string => {
    if (isStepActive(index) || isStepCompleted(index)) {
      return '#FFFFFF';
    }
    return theme.colors.textSecondary;
  };

  /**
   * Get label text style
   */
  const getLabelStyle = (index: number): object => {
    return {
      color: isStepActive(index)
        ? theme.colors.primary
        : isStepCompleted(index)
        ? theme.colors.success
        : theme.colors.textSecondary,
      fontWeight: isStepActive(index) ? '600' : '400',
    };
  };

  /**
   * Calculate progress bar width based on current step position
   */
  const getProgressWidth = (): `${number}%` => {
    if (steps.length <= 1) return '0%';
    const progress = (currentIndex / (steps.length - 1)) * 100;
    return `${progress}%`;
  };

  return (
    <View style={styles.container}>
      {/* Progress Bar Background */}
      <View
        style={[
          styles.progressBarBackground,
          { backgroundColor: theme.colors.border },
        ]}
      >
        <View
          style={[
            styles.progressBarFill,
            { backgroundColor: theme.colors.primary, width: getProgressWidth() },
          ]}
        />
      </View>

      {/* Steps */}
      <View style={styles.stepsContainer}>
        {steps.map((step, index) => (
          <TouchableOpacity
            key={step.id}
            style={styles.stepContainer}
            onPress={() => onStepPress?.(step.id)}
            disabled={!onStepPress}
            accessibilityLabel={`Step ${index + 1}: ${step.label}`}
            accessibilityRole={onStepPress ? 'button' : 'text'}
            accessibilityState={{
              selected: isStepActive(index),
            }}
          >
            <View
              style={[
                styles.circle,
                {
                  backgroundColor: getCircleBackground(index),
                  borderColor: getCircleBorderColor(index),
                },
              ]}
            >
              <Text style={[styles.icon, { color: getIconColor(index) }]}>
                {getStepIcon(step, index)}
              </Text>
            </View>
            <Text style={[styles.label, getLabelStyle(index)]}>
              {step.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    paddingVertical: 16,
  },
  progressBarBackground: {
    height: 4,
    borderRadius: 2,
    position: 'absolute',
    top: 32,
    left: 40,
    right: 40,
    zIndex: 0,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  stepsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 16,
    zIndex: 1,
  },
  stepContainer: {
    alignItems: 'center',
    flex: 1,
  },
  circle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    marginBottom: 8,
  },
  icon: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  label: {
    fontSize: 12,
    textAlign: 'center',
  },
});

export default StepIndicator;
