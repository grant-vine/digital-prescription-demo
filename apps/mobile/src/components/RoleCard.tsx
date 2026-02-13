import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  useWindowDimensions,
  ScrollView,
} from 'react-native';
import { DoctorTheme } from '@/components/theme/DoctorTheme';
import { PatientTheme } from '@/components/theme/PatientTheme';
import { PharmacistTheme } from '@/components/theme/PharmacistTheme';

/**
 * Represents information about a user role in the system
 * @interface RoleInfo
 */
export interface RoleInfo {
  /** Unique identifier for the role */
  id: 'doctor' | 'patient' | 'pharmacist';
  /** Display title for the role */
  title: string;
  /** Short description of the role's purpose */
  description: string;
  /** Primary color for the role (hex code) */
  color: string;
  /** Emoji or text icon representing the role */
  icon: string;
  /** List of responsibilities for this role */
  responsibilities: string[];
  /** Estimated time to complete demo as this role */
  estimatedTime: string;
}

/**
 * Props for the RoleCard component
 * @interface RoleCardProps
 */
export interface RoleCardProps {
  /** Role information to display */
  role: RoleInfo;
  /** Callback when the card is pressed to navigate */
  onPress: () => void;
  /** Whether the card is currently expanded */
  expanded?: boolean;
  /** Callback when the expand/collapse button is pressed */
  onToggleExpand?: () => void;
  /** Optional test ID for testing */
  testID?: string;
}

/**
 * Predefined role information for all three roles
 * @example
 * ```tsx
 * import { ROLE_INFO } from '@/components/RoleCard';
 * 
 * function MyComponent() {
 *   return (
 *     <View>
 *       {ROLE_INFO.map(role => (
 *         <RoleCard key={role.id} role={role} onPress={() => {}} />
 *       ))}
 *     </View>
 *   );
 * }
 * ```
 */
export const ROLE_INFO: RoleInfo[] = [
  {
    id: 'doctor',
    title: 'Healthcare Provider',
    description: 'Create, sign, and issue digital prescriptions to patients',
    color: '#2563EB',
    icon: '👨‍⚕️',
    responsibilities: [
      'Authenticate and setup professional DID',
      'Search patient records',
      'Create prescriptions with medications',
      'Digitally sign using W3C Verifiable Credentials',
      'Generate QR codes for patients',
    ],
    estimatedTime: '2-3 minutes',
  },
  {
    id: 'patient',
    title: 'Patient',
    description: 'Receive, store, and share digital prescriptions securely',
    color: '#0891B2',
    icon: '🤒',
    responsibilities: [
      'Setup digital wallet with personal DID',
      'Scan QR codes to receive prescriptions',
      'View and manage prescription history',
      'Share prescriptions with pharmacists via QR',
      'Track prescription status',
    ],
    estimatedTime: '2-3 minutes',
  },
  {
    id: 'pharmacist',
    title: 'Pharmacist',
    description: 'Verify prescription authenticity and dispense medications',
    color: '#059669',
    icon: '💊',
    responsibilities: [
      'Authenticate as licensed pharmacist',
      'Scan and verify prescription QR codes',
      'Validate digital signatures',
      'Dispense medications with audit trail',
      'Update prescription status',
    ],
    estimatedTime: '1-2 minutes',
  },
];

/**
 * RoleCard - A card component displaying role information with expand/collapse functionality.
 *
 * Features:
 * - Role color accent border on left (4px)
 * - Header with icon, title, and estimated completion time
 * - Always-visible description
 * - Expand/collapse animation for responsibilities list
 * - "Continue as [role]" action button
 * - Responsive design adapts to screen width (mobile/desktop)
 * - Smooth height animation using React Animated API
 * - Fully accessible with ARIA labels and expanded state
 *
 * @param {RoleInfo} role - Role information object with id, title, description, color, icon, responsibilities, estimatedTime
 * @param {Function} onPress - Callback when Continue button is pressed, typically navigates to role flow
 * @param {boolean} [expanded=false] - Whether the card is currently expanded showing responsibilities
 * @param {Function} [onToggleExpand] - Callback when expand/collapse button is pressed
 * @param {string} [testID] - Optional test ID for testing purposes
 * @returns {React.ReactElement} The role card component with animation support
 *
 * @example
 * ```tsx
 * function RoleSelector() {
 *   const [expandedRole, setExpandedRole] = useState<string | null>(null);
 *   const router = useRouter();
 *
 *   return (
 *     <View>
 *       {ROLE_INFO.map(role => (
 *         <RoleCard
 *           key={role.id}
 *           role={role}
 *           expanded={expandedRole === role.id}
 *           onToggleExpand={() => setExpandedRole(
 *             expandedRole === role.id ? null : role.id
 *           )}
 *           onPress={() => router.push(`/${role.id}/auth`)}
 *           testID={`role-card-${role.id}`}
 *         />
 *       ))}
 *     </View>
 *   );
 * }
 * 
 * // Single role card
 * <RoleCard
 *   role={ROLE_INFO[0]}
 *   expanded
 *   onToggleExpand={() => setExpanded(!expanded)}
 *   onPress={() => navigateToDoctor()}
 * />
 * ```
 */
export function RoleCard({
  role,
  onPress,
  expanded = false,
  onToggleExpand,
  testID,
}: RoleCardProps): React.ReactElement {
  const { width } = useWindowDimensions();
  const isMobile = width < 768;

  // Get theme based on role
  const getTheme = () => {
    switch (role.id) {
      case 'doctor':
        return DoctorTheme;
      case 'patient':
        return PatientTheme;
      case 'pharmacist':
        return PharmacistTheme;
      default:
        return PatientTheme;
    }
  };

  const theme = getTheme();

  // Animation setup
  const heightAnim = useRef(new Animated.Value(0)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const [contentHeight, setContentHeight] = useState(0);

  useEffect(() => {
    if (expanded) {
      Animated.parallel([
        Animated.timing(heightAnim, {
          toValue: contentHeight,
          duration: 300,
          useNativeDriver: false,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 200,
          delay: 100,
          useNativeDriver: false,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(heightAnim, {
          toValue: 0,
          duration: 250,
          useNativeDriver: false,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0,
          duration: 150,
          useNativeDriver: false,
        }),
      ]).start();
    }
  }, [expanded, contentHeight, heightAnim, opacityAnim]);

  const handleExpandToggle = (): void => {
    onToggleExpand?.();
  };

  return (
    <View
      style={[
        styles.container,
        {
          borderLeftColor: role.color,
          backgroundColor: theme.colors.surface,
          maxWidth: isMobile ? '100%' : 400,
        },
      ]}
      testID={testID}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Text style={styles.icon}>{role.icon}</Text>
        </View>
        <View style={styles.headerText}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            {role.title}
          </Text>
          <Text style={[styles.estimatedTime, { color: theme.colors.textSecondary }]}>
            ⏱ {role.estimatedTime}
          </Text>
        </View>
      </View>

      {/* Description */}
      <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
        {role.description}
      </Text>

      {/* Expand/Collapse Button */}
      <TouchableOpacity
        style={styles.expandButton}
        onPress={handleExpandToggle}
        accessibilityLabel={expanded ? 'Collapse details' : 'Expand details'}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
      >
        <Text style={[styles.expandButtonText, { color: role.color }]}>
          {expanded ? 'Show less' : 'Learn more'}
        </Text>
        <Text style={[styles.chevron, { color: role.color }]}>
          {expanded ? '▼' : '▶'}
        </Text>
      </TouchableOpacity>

      {/* Expandable Content */}
      <Animated.View style={[styles.expandableContent, { height: heightAnim }]}>
        <View
          style={styles.contentWrapper}
          onLayout={(event): void => {
            setContentHeight(event.nativeEvent.layout.height);
          }}
        >
          <View style={styles.responsibilitiesSection}>
            <Text style={[styles.responsibilitiesTitle, { color: theme.colors.text }]}>
              What you'll do:
            </Text>
            <ScrollView style={styles.responsibilitiesList} showsVerticalScrollIndicator={false}>
              {role.responsibilities.map((responsibility) => (
                <View key={responsibility} style={styles.responsibilityItem}>
                  <Text style={[styles.bullet, { color: role.color }]}>•</Text>
                  <Text style={[styles.responsibilityText, { color: theme.colors.textSecondary }]}>
                    {responsibility}
                  </Text>
                </View>
              ))}
            </ScrollView>
          </View>
        </View>
      </Animated.View>

      {/* Continue Button */}
      <TouchableOpacity
        style={[styles.continueButton, { backgroundColor: role.color }]}
        onPress={onPress}
        accessibilityLabel={`Continue as ${role.title}`}
        accessibilityRole="button"
      >
        <Text style={styles.continueButtonText}>
          Continue as {role.title.split(' ')[0]}
        </Text>
        <Text style={styles.continueArrow}>→</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  icon: {
    fontSize: 24,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 2,
  },
  estimatedTime: {
    fontSize: 13,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    marginBottom: 12,
    paddingVertical: 4,
    paddingHorizontal: 8,
    marginLeft: -8,
  },
  expandButtonText: {
    fontSize: 14,
    fontWeight: '600',
    marginRight: 4,
  },
  chevron: {
    fontSize: 12,
  },
  expandableContent: {
    overflow: 'hidden',
  },
  contentWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
  },
  responsibilitiesSection: {
    marginBottom: 16,
  },
  responsibilitiesTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  responsibilitiesList: {
    maxHeight: 150,
  },
  responsibilityItem: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  bullet: {
    fontSize: 16,
    marginRight: 8,
    lineHeight: 20,
  },
  responsibilityText: {
    fontSize: 13,
    lineHeight: 20,
    flex: 1,
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginTop: 4,
  },
  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  continueArrow: {
    color: '#FFFFFF',
    fontSize: 18,
    marginLeft: 8,
  },
});

export default RoleCard;
