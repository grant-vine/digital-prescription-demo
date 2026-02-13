import React, { ErrorInfo, ReactNode } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { PatientTheme } from '@/components/theme/PatientTheme';

/**
 * Props for the ErrorBoundary component
 * @interface Props
 */
interface Props {
  /** Child components to render and monitor for errors */
  children: ReactNode;
}

/**
 * State for the ErrorBoundary component
 * @interface State
 */
interface State {
  /** Whether an error has occurred */
  hasError: boolean;
  /** The caught error object */
  error?: Error;
  /** Additional error information */
  errorInfo?: ErrorInfo;
}

/**
 * ErrorBoundary - An error boundary component that catches JavaScript errors in child components.
 * 
 * Features:
 * - Catches errors using React class component lifecycle methods
 * - Displays user-friendly error screen with restart button
 * - Shows detailed error information in development mode
 * - Follows React best practices for error boundaries
 * - Scrollable error details for long stack traces
 * - Accessible with proper ARIA labels and roles
 * 
 * @param {React.ReactNode} children - Child components to render and monitor for errors
 * @returns {React.ReactNode} Either the children if no error, or error UI if error caught
 * 
 * @example
 * ```tsx
 * // Wrap your entire app
 * <ErrorBoundary>
 *   <YourApp />
 * </ErrorBoundary>
 * 
 * // Wrap specific sections
 * <View>
 *   <ErrorBoundary>
 *     <ComplexFeature />
 *   </ErrorBoundary>
 *   <OtherFeature />
 * </View>
 * 
 * // In your app entry point
 * export default function RootLayout() {
 *   return (
 *     <ErrorBoundary>
 *       <Stack>
 *         <Stack.Screen name="index" component={HomeScreen} />
 *         <Stack.Screen name="details" component={DetailsScreen} />
 *       </Stack>
 *     </ErrorBoundary>
 *   );
 * }
 * ```
 */
export class ErrorBoundary extends React.Component<Props, State> {
  /**
   * Initialize state
   */
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  /**
   * Update state when an error is caught
   * This is a static method required by React for error boundaries
   */
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  /**
   * Log error details when caught
   * This lifecycle method runs after an error is caught
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Log to console in development
    if (__DEV__) {
      console.error('ErrorBoundary caught an error:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }

    // In production, you might send to an error reporting service
    // Example: Sentry.captureException(error);
  }

  /**
   * Handle restart button press
   * Reloads the app to reset state
   */
  handleRestart = (): void => {
    // Reset state to allow re-rendering
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    
    // In a real app, you might use expo-updates to reload
    // For now, we just reset the state
    if (__DEV__) {
      console.log('App restarted from error boundary');
    }
  };

  render(): ReactNode {
    const theme = PatientTheme;

    if (this.state.hasError) {
      return (
        <View
          style={[
            styles.container,
            { backgroundColor: theme.colors.background },
          ]}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator
          >
            {/* Error Icon */}
            <Text style={styles.errorIcon}>⚠️</Text>

            {/* Title */}
            <Text style={[styles.title, { color: theme.colors.text }]}>
              Demo Temporarily Unavailable
            </Text>

            {/* Message */}
            <Text
              style={[
                styles.message,
                { color: theme.colors.textSecondary },
              ]}
            >
              An unexpected error occurred. Please restart the demo.
            </Text>

            {/* Restart Button */}
            <TouchableOpacity
              style={[
                styles.restartButton,
                { backgroundColor: theme.colors.primary },
              ]}
              onPress={this.handleRestart}
              accessibilityLabel="Restart the demo"
              accessibilityRole="button"
            >
              <Text style={styles.restartButtonText}>Restart Demo</Text>
            </TouchableOpacity>

            {/* Contact Info */}
            <View style={styles.contactContainer}>
              <Text
                style={[
                  styles.contactText,
                  { color: theme.colors.textSecondary },
                ]}
              >
                If the problem persists, please contact support.
              </Text>
            </View>

            {/* Development Error Details */}
            {__DEV__ && this.state.error && (
              <View
                style={[
                  styles.errorDetails,
                  { backgroundColor: theme.colors.surface },
                ]}
              >
                <Text
                  style={[
                    styles.errorDetailsTitle,
                    { color: theme.colors.error },
                  ]}
                >
                  Error Details (Development Mode):
                </Text>
                <Text
                  style={[
                    styles.errorDetailsText,
                    { color: theme.colors.text },
                  ]}
                >
                  {this.state.error.toString()}
                </Text>
                {this.state.errorInfo && (
                  <Text
                    style={[
                      styles.errorStackText,
                      { color: theme.colors.textSecondary },
                    ]}
                  >
                    {this.state.errorInfo.componentStack}
                  </Text>
                )}
              </View>
            )}
          </ScrollView>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  message: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  restartButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
    marginBottom: 24,
  },
  restartButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  contactContainer: {
    marginTop: 16,
  },
  contactText: {
    fontSize: 14,
    textAlign: 'center',
  },
  errorDetails: {
    width: '100%',
    marginTop: 32,
    padding: 16,
    borderRadius: 8,
  },
  errorDetailsTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  errorDetailsText: {
    fontSize: 12,
    fontFamily: 'monospace',
  },
  errorStackText: {
    fontSize: 10,
    fontFamily: 'monospace',
    marginTop: 8,
  },
});

export default ErrorBoundary;
