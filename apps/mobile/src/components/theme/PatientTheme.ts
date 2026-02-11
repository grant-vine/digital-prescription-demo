/**
 * Patient Theme
 * Primary Color: Cyan (#0891B2)
 * Styling: Mobile-first personal health
 */

export const PatientTheme = {
  colors: {
    primary: '#0891B2',
    secondary: '#0e7490',
    background: '#f0f9fa',
    surface: '#ffffff',
    text: '#164e63',
    textSecondary: '#06b6d4',
    border: '#cffafe',
    success: '#059669',
    warning: '#f59e0b',
    error: '#dc2626',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    h1: { fontSize: 32, fontWeight: 'bold' },
    h2: { fontSize: 24, fontWeight: 'bold' },
    h3: { fontSize: 20, fontWeight: '600' },
    body: { fontSize: 16, fontWeight: '400' },
    small: { fontSize: 14, fontWeight: '400' },
  },
};

export type PatientThemeType = typeof PatientTheme;
