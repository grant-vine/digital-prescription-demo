import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  StyleSheet,
  ScrollView,
  TouchableWithoutFeedback,
  Dimensions,
} from 'react-native';
import { PatientTheme } from '@/components/theme/PatientTheme';

/**
 * Props for the InfoTooltip component
 * @interface InfoTooltipProps
 */
export interface InfoTooltipProps {
  /** Title displayed in the modal header */
  title: string;
  /** Content text displayed in the modal (scrollable) */
  content: string;
  /** Icon type to display (default: 'info') */
  icon?: 'info' | 'help' | 'alert';
}

const { height: screenHeight } = Dimensions.get('window');

/**
 * InfoTooltip - A tooltip component that displays information in a modal when pressed.
 * 
 * Features:
 * - Small circular button with icon
 * - Opens a modal with title and scrollable content
 * - Semi-transparent backdrop
 * - Close button at the bottom
 * - Accessible with proper ARIA labels
 * 
 * @param {string} title - Title displayed in the modal header
 * @param {string} content - Content text displayed in the modal (scrollable)
 * @param {'info' | 'help' | 'alert'} [icon='info'] - Icon type to display (info, help, or alert)
 * @returns {React.ReactElement} The tooltip button and modal component
 * 
 * @example
 * ```tsx
 * <InfoTooltip
 *   title="Prescription Information"
 *   content="This prescription is valid for 30 days from the issue date."
 * />
 * 
 * <InfoTooltip
 *   title="Security Notice"
 *   content="Your data is encrypted and stored securely."
 *   icon="alert"
 * />
 * 
 * <View style={{ flexDirection: 'row' }}>
 *   <Text>What is a DID?</Text>
 *   <InfoTooltip
 *     title="Decentralized Identifier"
 *     content="A DID (Decentralized Identifier) is a unique identifier that you control..."
 *     icon="help"
 *   />
 * </View>
 * ```
 */
export function InfoTooltip({
  title,
  content,
  icon = 'info',
}: InfoTooltipProps): React.ReactElement {
  const theme = PatientTheme;
  const [modalVisible, setModalVisible] = useState(false);

  /**
   * Get the appropriate icon symbol based on icon type
   */
  const getIconSymbol = (): string => {
    switch (icon) {
      case 'info':
        return 'ℹ';
      case 'help':
        return '?';
      case 'alert':
        return '⚠';
      default:
        return 'ℹ';
    }
  };

  /**
   * Get the icon color based on icon type
   */
  const getIconColor = (): string => {
    switch (icon) {
      case 'alert':
        return theme.colors.warning;
      default:
        return theme.colors.primary;
    }
  };

  return (
    <View>
      <TouchableOpacity
        style={[
          styles.button,
          { backgroundColor: `${getIconColor()}20` },
        ]}
        onPress={() => setModalVisible(true)}
        accessibilityLabel={`Show information about ${title}`}
        accessibilityRole="button"
      >
        <Text style={[styles.icon, { color: getIconColor() }]}>
          {getIconSymbol()}
        </Text>
      </TouchableOpacity>

      <Modal
        animationType="fade"
        transparent
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
        accessibilityViewIsModal
      >
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <View style={styles.modalOverlay}>
            <TouchableWithoutFeedback>
              <View
                style={[
                  styles.modalContent,
                  { backgroundColor: theme.colors.surface },
                ]}
              >
                <View style={styles.header}>
                  <Text style={[styles.iconLarge, { color: getIconColor() }]}>
                    {getIconSymbol()}
                  </Text>
                  <Text style={[styles.title, { color: theme.colors.text }]}>
                    {title}
                  </Text>
                </View>

                <ScrollView
                  style={styles.scrollView}
                  showsVerticalScrollIndicator
                  contentContainerStyle={styles.scrollContent}
                >
                  <Text
                    style={[
                      styles.content,
                      { color: theme.colors.textSecondary },
                    ]}
                  >
                    {content}
                  </Text>
                </ScrollView>

                <TouchableOpacity
                  style={[
                    styles.closeButton,
                    { backgroundColor: theme.colors.primary },
                  ]}
                  onPress={() => setModalVisible(false)}
                  accessibilityLabel="Close information modal"
                  accessibilityRole="button"
                >
                  <Text style={styles.closeButtonText}>Close</Text>
                </TouchableOpacity>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    fontSize: 16,
    fontWeight: 'bold',
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    width: '100%',
    maxWidth: 400,
    maxHeight: screenHeight * 0.7,
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  iconLarge: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    flex: 1,
  },
  scrollView: {
    maxHeight: screenHeight * 0.4,
  },
  scrollContent: {
    paddingBottom: 8,
  },
  content: {
    fontSize: 16,
    lineHeight: 24,
  },
  closeButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default InfoTooltip;
