/**
 * Doctor Theme
 * Primary Color: Royal Blue (#2563EB)
 * Styling: Clinical professional layout
 */

export const DoctorTheme = {
  colors: {
    primary: '#2563EB',
    secondary: '#1e40af',
    background: '#f8fafc',
    surface: '#ffffff',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
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

export type DoctorThemeType = typeof DoctorTheme;
