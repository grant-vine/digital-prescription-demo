import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  useWindowDimensions,
} from 'react-native';
import { DoctorTheme } from './theme/DoctorTheme';
import { PatientTheme } from './theme/PatientTheme';
import { PharmacistTheme } from './theme/PharmacistTheme';

/**
 * Represents a step in the prescription workflow
 * @interface WorkflowStep
 */
export interface WorkflowStep {
  /** Step number (1-4) */
  step: number;
  /** Role responsible for this step */
  role: 'doctor' | 'patient' | 'pharmacist' | 'system';
  /** Short action label */
  action: string;
  /** Detailed description of what happens */
  description: string;
  /** Emoji or text icon */
  icon: string;
}

/**
 * Predefined workflow steps for the digital prescription process
 * @example
 * ```tsx
 * import { WORKFLOW_STEPS } from '@/components/WorkflowDiagram';
 * 
 * function MyComponent() {
 *   return (
 *     <View>
 *       {WORKFLOW_STEPS.map(step => (
 *         <Text key={step.step}>{step.action}</Text>
 *       ))}
 *     </View>
 *   );
 * }
 * ```
 */
export const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    step: 1,
    role: 'doctor',
    action: 'Creates',
    description: 'Doctor creates and signs prescription',
    icon: '📝',
  },
  {
    step: 2,
    role: 'patient',
    action: 'Receives',
    description: 'Patient scans QR and stores in wallet',
    icon: '📱',
  },
  {
    step: 3,
    role: 'pharmacist',
    action: 'Verifies',
    description: 'Pharmacist checks signature and dispenses',
    icon: '✓',
  },
  {
    step: 4,
    role: 'system',
    action: 'Audits',
    description: 'Complete audit trail recorded',
    icon: '📋',
  },
];

/**
 * Props for the WorkflowDiagram component
 * @interface WorkflowDiagramProps
 */
export interface WorkflowDiagramProps {
  /** Optional test ID for testing */
  testID?: string;
}

/**
 * WorkflowDiagram - A responsive workflow diagram showing the digital prescription process.
 *
 * Features:
 * - Mobile (<768px): Vertical layout with connecting lines between steps
 * - Desktop (>=768px): Horizontal layout with arrow connectors between steps
 * - Color-coded steps by role (doctor=blue, patient=cyan, pharmacist=green, system=gray)
 * - Fully accessible with ARIA labels for each step
 * - Step numbers, icons, and descriptions for visual clarity
 * - Smooth responsive transitions between mobile and desktop layouts
 * - Self-contained with predefined workflow steps
 *
 * @param {string} [testID] - Optional test ID for testing purposes
 * @returns {React.ReactElement} The responsive workflow diagram component
 *
 * @example
 * ```tsx
 * // Basic usage
 * <WorkflowDiagram />
 * 
 * // In a scrollable container
 * <ScrollView>
 *   <Text style={{ fontSize: 24, fontWeight: 'bold' }}>How Digital Prescriptions Work</Text>
 *   <WorkflowDiagram testID="prescription-workflow" />
 *   <Text>Each step is verified and recorded in the audit trail.</Text>
 * </ScrollView>
 * 
 * // On role selection screen
 * function RoleSelectionPage() {
 *   return (
 *     <View style={{ flex: 1 }}>
 *       <WorkflowDiagram />
 *       <RoleCard role={doctorRole} onPress={handleDoctorSelect} />
 *       <RoleCard role={patientRole} onPress={handlePatientSelect} />
 *       <RoleCard role={pharmacistRole} onPress={handlePharmacistSelect} />
 *     </View>
 *   );
 * }
 * ```
 */
export function WorkflowDiagram({ testID }: WorkflowDiagramProps): React.ReactElement {
  const { width } = useWindowDimensions();
  const isMobile = width < 768;

  /**
   * Get the color for a step based on its role
   */
  const getStepColor = (role: WorkflowStep['role']): string => {
    switch (role) {
      case 'doctor':
        return DoctorTheme.colors.primary;
      case 'patient':
        return PatientTheme.colors.primary;
      case 'pharmacist':
        return PharmacistTheme.colors.primary;
      case 'system':
        return '#64748b'; // Gray for system
      default:
        return '#64748b';
    }
  };

  /**
   * Get the background color for a step based on its role
   */
  const getStepBackgroundColor = (role: WorkflowStep['role']): string => {
    switch (role) {
      case 'doctor':
        return '#eff6ff'; // Light blue
      case 'patient':
        return '#ecfeff'; // Light cyan
      case 'pharmacist':
        return '#f0fdf4'; // Light green
      case 'system':
        return '#f1f5f9'; // Light gray
      default:
        return '#f1f5f9';
    }
  };

  /**
   * Render a single step in the workflow
   */
  const renderStep = (stepData: WorkflowStep, index: number): React.ReactElement => {
    const color = getStepColor(stepData.role);
    const backgroundColor = getStepBackgroundColor(stepData.role);
    const isLast = index === WORKFLOW_STEPS.length - 1;

    return (
      <View
        key={stepData.step}
        testID={`workflow-step-${stepData.step}`}
        style={[
          styles.stepContainer,
          isMobile ? styles.stepContainerMobile : styles.stepContainerDesktop,
        ]}
        accessibilityLabel={`Step ${stepData.step}: ${stepData.description}`}
        accessibilityRole="text"
      >
        {/* Connector Line (Mobile: top-to-bottom, Desktop: left-to-right) */}
        {!isLast && (
          <View
            style={[
              styles.connector,
              isMobile ? styles.connectorMobile : styles.connectorDesktop,
              { backgroundColor: color },
            ]}
          />
        )}

        {/* Step Circle */}
        <View
          style={[
            styles.stepCircle,
            { backgroundColor, borderColor: color },
          ]}
        >
          <Text style={[styles.stepIcon, { color }]}>{stepData.icon}</Text>
        </View>

        {/* Step Content */}
        <View style={[styles.stepContent, isMobile ? styles.stepContentMobile : styles.stepContentDesktop]}>
          <Text style={[styles.stepNumber, { color }]}>Step {stepData.step}</Text>
          <Text style={[styles.stepAction, { color }]}>{stepData.action}</Text>
          <Text style={styles.stepDescription}>{stepData.description}</Text>
        </View>

        {/* Arrow Connector (Desktop only, except last step) */}
        {!isLast && !isMobile && (
          <View style={styles.arrowContainer}>
            <Text style={[styles.arrow, { color }]}>→</Text>
          </View>
        )}
      </View>
    );
  };

  return (
    <View
      style={[
        styles.container,
        isMobile ? styles.containerMobile : styles.containerDesktop,
      ]}
      testID={testID}
    >
      <Text style={styles.title}>How It Works</Text>
      <View
        style={[
          styles.stepsWrapper,
          isMobile ? styles.stepsWrapperMobile : styles.stepsWrapperDesktop,
        ]}
      >
        {WORKFLOW_STEPS.map((step, index) => renderStep(step, index))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 24,
    marginVertical: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  containerMobile: {
    marginHorizontal: 16,
  },
  containerDesktop: {
    marginHorizontal: 32,
    maxWidth: 1200,
    alignSelf: 'center',
    width: '100%',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e293b',
    textAlign: 'center',
    marginBottom: 24,
  },
  stepsWrapper: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  stepsWrapperMobile: {
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  stepsWrapperDesktop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
  },
  stepContainer: {
    alignItems: 'center',
    position: 'relative',
  },
  stepContainerMobile: {
    flexDirection: 'row',
    marginBottom: 24,
    paddingLeft: 8,
  },
  stepContainerDesktop: {
    flexDirection: 'column',
    alignItems: 'center',
    flex: 1,
    minWidth: 180,
    maxWidth: 220,
  },
  connector: {
    position: 'absolute',
  },
  connectorMobile: {
    width: 2,
    height: 40,
    left: 31,
    top: 56,
    zIndex: 0,
  },
  connectorDesktop: {
    display: 'none',
  },
  stepCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    zIndex: 1,
  },
  stepIcon: {
    fontSize: 28,
  },
  stepContent: {
    alignItems: 'center',
  },
  stepContentMobile: {
    marginLeft: 16,
    alignItems: 'flex-start',
    flex: 1,
  },
  stepContentDesktop: {
    marginTop: 12,
    alignItems: 'center',
    textAlign: 'center',
  },
  stepNumber: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  stepAction: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 13,
    color: '#64748b',
    lineHeight: 18,
    textAlign: 'center',
  },
  arrowContainer: {
    position: 'absolute',
    right: -20,
    top: 20,
  },
  arrow: {
    fontSize: 24,
    fontWeight: 'bold',
  },
});

export default WorkflowDiagram;
