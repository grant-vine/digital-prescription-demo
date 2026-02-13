import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { PatientTheme } from '@/components/theme/PatientTheme';

/**
 * Props for the CardContainer component
 * @interface CardContainerProps
 */
export interface CardContainerProps {
  /** Child elements to render inside the card */
  children: React.ReactNode;
  /** Maximum width of the card in pixels (default: 480) */
  maxWidth?: number;
}

const { width: screenWidth } = Dimensions.get('window');

/**
 * A container component that wraps content in a styled card.
 * 
 * Features:
 * - White background with subtle shadow
 * - Rounded corners
 * - Consistent padding
 * - Max-width constraint that's centered on larger screens
 * - Responsive to screen size
 * 
 * @example
 * ```tsx
 * <CardContainer>
 *   <Text>Your content here</Text>
 * </CardContainer>
 * 
 * <CardContainer maxWidth={600}>
 *   <Text>Wider card for larger content</Text>
 * </CardContainer>
 * ```
 */
export function CardContainer({
  children,
  maxWidth = 480,
}: CardContainerProps): React.ReactElement {
  const theme = PatientTheme;

  /**
   * Calculate the actual width to use
   * - On small screens: full width minus padding
   * - On large screens: maxWidth constraint
   */
  const calculatedWidth = Math.min(screenWidth - theme.spacing.lg * 2, maxWidth);

  return (
    <View style={styles.outerContainer}>
      <View
        style={[
          styles.card,
          {
            backgroundColor: theme.colors.surface,
            maxWidth: maxWidth,
            width: calculatedWidth,
          },
        ]}
      >
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
});

export default CardContainer;
