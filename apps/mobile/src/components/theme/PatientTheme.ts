export const PatientTheme = {
  colors: {
    primary: '#0891B2',        // Cyan (main action color)
    secondary: '#0e7490',      // Darker cyan (secondary actions)
    background: '#F0F9FF',     // Light cyan background
    surface: '#FFFFFF',        // White cards
    text: '#0C4A6E',          // Dark cyan text
    textSecondary: '#075985', // Medium cyan
    error: '#DC2626',         // Red errors
    success: '#059669',       // Green success
    border: '#cffafe',        // Kept from original
    warning: '#f59e0b',       // Kept from original
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    h1: { fontSize: 32, fontWeight: 'bold' as const },
    h2: { fontSize: 24, fontWeight: 'bold' as const },
    h3: { fontSize: 20, fontWeight: '600' as const },
    body: { fontSize: 16, fontWeight: '400' as const },
    small: { fontSize: 14, fontWeight: '400' as const },
    title: {
      fontSize: 28,
      fontWeight: 'bold' as const,
    },
    heading: {
      fontSize: 20,
      fontWeight: '600' as const,
    },
    caption: {
      fontSize: 14,
      color: '#64748B',
    },
  },
};

export type PatientThemeType = typeof PatientTheme;
