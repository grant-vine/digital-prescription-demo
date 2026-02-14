import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Animated,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { RoleCard, ROLE_INFO } from '../components/RoleCard';
import { WorkflowDiagram } from '../components/WorkflowDiagram';

/**
 * FAQ item data structure
 * @interface FAQItem
 */
interface FAQItem {
  /** Question text */
  question: string;
  /** Answer text */
  answer: string;
}

/**
 * FAQ data for the Quick Start guide
 */
const FAQ_ITEMS: FAQItem[] = [
  {
    question: 'How the Demo Works',
    answer:
      'This demo showcases Self-Sovereign Identity (SSI) technology for digital prescriptions. Choose a role, complete the authentication flow, and experience the secure prescription workflow from creation to dispensing.',
  },
  {
    question: 'What is SSI?',
    answer:
      'Self-Sovereign Identity allows individuals to own and control their digital identities without relying on centralized authorities. In this demo, doctors, patients, and pharmacists each have decentralized identifiers (DIDs) for secure, verifiable interactions.',
  },
  {
    question: 'QR Code Flow',
    answer:
      'Prescriptions are shared via QR codes containing encrypted verifiable credentials. Patients scan to receive, pharmacists scan to verify. All interactions are cryptographically signed and auditable.',
  },
  {
    question: 'Total Demo Time',
    answer:
      '3-5 minutes for complete workflow (doctor creates, patient receives, pharmacist dispenses)',
  },
];

/**
 * Props for individual FAQ accordion item
 * @interface FAQAccordionItemProps
 */
interface FAQAccordionItemProps {
  /** FAQ item data */
  item: FAQItem;
  /** Whether this item is expanded */
  expanded: boolean;
  /** Callback to toggle expansion */
  onToggle: () => void;
  /** Index for accessibility labeling */
  index: number;
}

/**
 * Individual FAQ accordion item with expand/collapse animation
 */
function FAQAccordionItem({
  item,
  expanded,
  onToggle,
  index,
}: FAQAccordionItemProps): React.ReactElement {
  const heightAnimRef = useRef<Animated.Value>(null);
  const opacityAnimRef = useRef<Animated.Value>(null);
  const [contentHeight, setContentHeight] = useState(0);

  // eslint-disable-next-line react-hooks/refs
  if (!heightAnimRef.current) {
    heightAnimRef.current = new Animated.Value(0);
  }
  // eslint-disable-next-line react-hooks/refs
  if (!opacityAnimRef.current) {
    opacityAnimRef.current = new Animated.Value(0);
  }

  useEffect(() => {
    if (!heightAnimRef.current || !opacityAnimRef.current) return;

    if (expanded) {
      Animated.parallel([
        Animated.timing(heightAnimRef.current, {
          toValue: contentHeight,
          duration: 250,
          useNativeDriver: false,
        }),
        Animated.timing(opacityAnimRef.current, {
          toValue: 1,
          duration: 200,
          delay: 50,
          useNativeDriver: false,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(heightAnimRef.current, {
          toValue: 0,
          duration: 200,
          useNativeDriver: false,
        }),
        Animated.timing(opacityAnimRef.current, {
          toValue: 0,
          duration: 150,
          useNativeDriver: false,
        }),
      ]).start();
    }
  }, [expanded, contentHeight]);

  return (
    <View style={styles.faqItem}>
      <TouchableOpacity
        style={styles.faqQuestionContainer}
        onPress={onToggle}
        accessibilityLabel={`FAQ ${index + 1}: ${item.question}`}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
      >
        <Text style={styles.faqQuestion}>{item.question}</Text>
        <Text style={[styles.faqChevron, expanded && styles.faqChevronExpanded]}>
          ▼
        </Text>
      </TouchableOpacity>
      {/* eslint-disable-next-line react-hooks/refs */}
      <Animated.View style={[styles.faqAnswerContainer, { height: heightAnimRef.current, opacity: opacityAnimRef.current }]}>
        <View
          style={styles.faqAnswerWrapper}
          onLayout={(event): void => {
            setContentHeight(event.nativeEvent.layout.height);
          }}
        >
          <Text style={styles.faqAnswer}>{item.answer}</Text>
        </View>
      </Animated.View>
    </View>
  );
}

/**
 * Quick Start guide component with FAQ accordion
 */
function QuickStartGuide(): React.ReactElement {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const handleToggle = (index: number): void => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  return (
    <View style={styles.quickStartContainer}>
      <Text style={styles.quickStartTitle}>Quick Start Guide</Text>
      <View style={styles.faqContainer}>
        {FAQ_ITEMS.map((item, index) => (
          <FAQAccordionItem
            key={item.question}
            item={item}
            index={index}
            expanded={expandedIndex === index}
            onToggle={() => handleToggle(index)}
          />
        ))}
      </View>
    </View>
  );
}

/**
 * Main role selector screen component
 *
 * Features:
 * - Workflow diagram showing the prescription process
 * - Role cards with expand/collapse for detailed information
 * - Quick Start FAQ guide with accordion
 * - Responsive layout adapting to mobile, tablet, and desktop
 * - Accessible navigation to role-specific flows
 */
export default function RoleSelector(): React.ReactElement {
  const [expandedRole, setExpandedRole] = useState<string | null>(null);
  const router = useRouter();
  const { width } = useWindowDimensions();
  const isDesktop = width >= 1024;
  const isTablet = width >= 768 && width < 1024;

  const navigateToRole = (roleId: string): void => {
    router.push(`/${roleId}/auth`);
  };

  const handleToggleExpand = (roleId: string): void => {
    setExpandedRole(expandedRole === roleId ? null : roleId);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Digital Prescription Demo</Text>
          <Text style={styles.subtitle}>
            Experience the future of secure, verifiable digital prescriptions
          </Text>
        </View>

        {/* Workflow Diagram */}
        <WorkflowDiagram />

        {/* Role Cards Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Choose Your Role</Text>
          <View
            style={[
              styles.rolesContainer,
              isDesktop && styles.rolesContainerDesktop,
              isTablet && styles.rolesContainerTablet,
            ]}
          >
            {ROLE_INFO.map((role) => (
              <RoleCard
                key={role.id}
                role={role}
                expanded={expandedRole === role.id}
                onToggleExpand={() => handleToggleExpand(role.id)}
                onPress={() => navigateToRole(role.id)}
                testID={`role-card-${role.id}`}
              />
            ))}
          </View>
        </View>

        {/* Quick Start Guide */}
        <QuickStartGuide />

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Powered by Self-Sovereign Identity (SSI) Technology
          </Text>
          <Text style={styles.footerSubtext}>W3C Verifiable Credentials • Decentralized Identifiers</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 32,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 16,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    maxWidth: 500,
  },
  section: {
    marginTop: 8,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 16,
    textAlign: 'center',
  },
  rolesContainer: {
    width: '100%',
  },
  rolesContainerTablet: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  rolesContainerDesktop: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 20,
    maxWidth: 1280,
    alignSelf: 'center',
  },
  quickStartContainer: {
    backgroundColor: '#f1f5f9',
    borderRadius: 16,
    padding: 24,
    marginHorizontal: 16,
    marginTop: 24,
    marginBottom: 16,
  },
  quickStartTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 16,
    textAlign: 'center',
  },
  faqContainer: {
    gap: 8,
  },
  faqItem: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  faqQuestionContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  faqQuestion: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
    flex: 1,
  },
  faqChevron: {
    fontSize: 14,
    color: '#64748b',
    marginLeft: 8,
    transform: [{ rotate: '0deg' }],
  },
  faqChevronExpanded: {
    transform: [{ rotate: '180deg' }],
  },
  faqAnswerContainer: {
    overflow: 'hidden',
  },
  faqAnswerWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  faqAnswer: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
  },
  footer: {
    marginTop: 24,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#64748b',
    marginBottom: 4,
  },
  footerSubtext: {
    fontSize: 12,
    color: '#94a3b8',
    textAlign: 'center',
  },
});
