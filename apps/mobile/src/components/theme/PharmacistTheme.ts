/**
 * Pharmacist Theme
 * Primary Color: Green (#059669)
 * Styling: Clinical dispensing workstation
 */

export const PharmacistTheme = {
  colors: {
    primary: '#059669',
    secondary: '#047857',
    background: '#f0fdf4',
    surface: '#ffffff',
    text: '#166534',
    textSecondary: '#16a34a',
    border: '#bbf7d0',
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

export type PharmacistThemeType = typeof PharmacistTheme;
