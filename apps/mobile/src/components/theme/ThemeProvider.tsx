/**
 * ThemeProvider Component
 * 
 * Provides role-specific themes throughout the React Native application using Context API.
 * Supports doctor (blue), patient (cyan), and pharmacist (green) themes.
 * 
 * Usage:
 * ```tsx
 * <ThemeProvider role="doctor">
 *   <App />
 * </ThemeProvider>
 * ```
 * 
 * Access theme in child components:
 * ```tsx
 * const theme = useTheme();
 * <View style={{ backgroundColor: theme.colors.primary }} />
 * ```
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { DoctorTheme } from './DoctorTheme';
import { PatientTheme } from './PatientTheme';
import { PharmacistTheme } from './PharmacistTheme';

/**
 * Theme type inferred from DoctorTheme structure.
 * All themes (Doctor, Patient, Pharmacist) follow the same structure.
 */
export type Theme = typeof DoctorTheme;

/**
 * Role type for theme selection.
 */
export type Role = 'doctor' | 'patient' | 'pharmacist';

/**
 * Theme context - undefined when outside provider.
 */
const ThemeContext = createContext<Theme | undefined>(undefined);

/**
 * ThemeProvider props interface.
 */
export interface ThemeProviderProps {
  role?: Role;
  children?: ReactNode;
}

/**
 * ThemeProvider component wraps the app and provides theme context.
 * 
 * @param role - User role ('doctor' | 'patient' | 'pharmacist'). Defaults to 'patient'.
 * @param children - Child components to render within the provider.
 * 
 * @example
 * ```tsx
 * <ThemeProvider role="doctor">
 *   <MyApp />
 * </ThemeProvider>
 * ```
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ 
  role = 'patient', 
  children 
}) => {
  // Select theme based on role
  const theme = selectThemeForRole(role);

  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Helper function to select appropriate theme based on user role.
 * 
 * @param role - User role
 * @returns Theme object (DoctorTheme, PatientTheme, or PharmacistTheme)
 */
function selectThemeForRole(role: Role): Theme {
  switch (role) {
    case 'doctor':
      return DoctorTheme;
    case 'patient':
      return PatientTheme;
    case 'pharmacist':
      return PharmacistTheme;
    default:
      // Fallback to patient theme (most common user)
      return PatientTheme;
  }
}

/**
 * useTheme hook provides access to the current theme.
 * Must be used within a ThemeProvider component.
 * 
 * @returns Current theme object with colors, spacing, and typography.
 * @throws Error if used outside ThemeProvider.
 * 
 * @example
 * ```tsx
 * function MyComponent() {
 *   const theme = useTheme();
 *   return (
 *     <View style={{ backgroundColor: theme.colors.primary }}>
 *       <Text style={{ color: theme.colors.text }}>Hello</Text>
 *     </View>
 *   );
 * }
 * ```
 */
export function useTheme(): Theme {
  const context = useContext(ThemeContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}
