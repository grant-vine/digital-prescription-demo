import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { PatientTheme } from './theme/PatientTheme';

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
 * CardContainer - A responsive container component that wraps content in a styled card.
 * 
 * Features:
 * - White/themed background with subtle shadow
 * - Rounded corners (12px)
 * - Consistent padding (24px)
 * - Max-width constraint that's centered on larger screens
 * - Responsive to screen size (adapts to mobile/tablet/desktop)
 * - Elevation effect for depth
 * 
 * @param {React.ReactNode} children - Child elements to render inside the card
 * @param {number} [maxWidth=480] - Maximum width of the card in pixels (default: 480)
 * @returns {React.ReactElement} The styled card container component
 * 
 * @example
 * ```tsx
 * <CardContainer>
 *   <Text style={{ fontSize: 18, fontWeight: '600' }}>Your content here</Text>
 * </CardContainer>
 * 
 * <CardContainer maxWidth={600}>
 *   <View>
 *     <Text>Title</Text>
 *     <Text>Wider card for larger content layouts</Text>
 *   </View>
 * </CardContainer>
 * 
 * <CardContainer maxWidth={500}>
 *   <ScrollView>
 *     <Text>Scrollable content inside a card</Text>
 *   </ScrollView>
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
