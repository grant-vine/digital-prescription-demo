export const PatientTheme = {
  colors: {
    primary: '#0891B2',        // Cyan (main action color)
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
    title: {
      fontSize: 28,
      fontWeight: 'bold',
    },
    heading: {
      fontSize: 20,
      fontWeight: '600',
    },
    body: {
      fontSize: 16,
    },
    caption: {
      fontSize: 14,
      color: '#64748B',
    },
    // Keep backward compatibility just in case
    h1: { fontSize: 32, fontWeight: 'bold' },
    h2: { fontSize: 24, fontWeight: 'bold' },
  },
};

export type PatientThemeType = typeof PatientTheme;
