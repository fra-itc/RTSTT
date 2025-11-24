/**
 * Design System Tokens
 * Centralized design values for the ORCHIDEA RTSTT application
 */

// Color Palette
export const colors = {
  // Primary colors
  primary: {
    main: '#1976d2',
    dark: '#115293',
    light: '#42a5f5',
    lighter: '#90caf9',
    contrast: '#ffffff',
  },
  // Secondary colors
  secondary: {
    main: '#dc004e',
    dark: '#9a0036',
    light: '#f48fb1',
    contrast: '#ffffff',
  },
  // Semantic colors
  success: {
    main: '#4caf50',
    dark: '#388e3c',
    light: '#66bb6a',
  },
  warning: {
    main: '#ff9800',
    dark: '#f57c00',
    light: '#ffa726',
  },
  error: {
    main: '#f44336',
    dark: '#d32f2f',
    light: '#ef5350',
  },
  info: {
    main: '#2196f3',
    dark: '#1976d2',
    light: '#64b5f6',
  },
  // Light theme
  light: {
    background: '#fafafa',
    surface: '#ffffff',
    textPrimary: '#212121',
    textSecondary: '#757575',
    border: '#e0e0e0',
    divider: '#eeeeee',
  },
  // Dark theme
  dark: {
    background: '#121212',
    surface: '#1e1e1e',
    textPrimary: '#ffffff',
    textSecondary: '#b0b0b0',
    border: '#2e2e2e',
    divider: '#2e2e2e',
  },
};

// Typography
export const typography = {
  fontFamily: {
    base: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"Fira Code", "Consolas", "Monaco", monospace',
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '2rem',    // 32px
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// Spacing System (based on 8px grid)
export const spacing = {
  xs: 4,    // 0.25rem
  sm: 8,    // 0.5rem
  md: 16,   // 1rem
  lg: 24,   // 1.5rem
  xl: 32,   // 2rem
  '2xl': 48,  // 3rem
  '3xl': 64,  // 4rem
};

// Border Radius
export const borderRadius = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  '2xl': 24,
  full: 9999,
};

// Elevation (Box Shadows)
export const elevation = {
  none: 'none',
  1: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08)',
  2: '0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)',
  3: '0 8px 12px rgba(0,0,0,0.15), 0 4px 8px rgba(0,0,0,0.1)',
  4: '0 12px 24px rgba(0,0,0,0.2), 0 8px 16px rgba(0,0,0,0.15)',
  5: '0 16px 32px rgba(0,0,0,0.25), 0 12px 24px rgba(0,0,0,0.2)',
};

// Breakpoints
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 960,
  lg: 1280,
  xl: 1920,
};

// Z-Index Layers
export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  modalBackdrop: 1300,
  modal: 1400,
  popover: 1500,
  tooltip: 1600,
  notification: 1700,
};

// Transitions
export const transitions = {
  duration: {
    shortest: 150,
    shorter: 200,
    short: 250,
    standard: 300,
    complex: 375,
    enteringScreen: 225,
    leavingScreen: 195,
  },
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  },
};

// Component-specific tokens
export const components = {
  appBar: {
    height: 64,
    heightMobile: 56,
  },
  sidebar: {
    width: 300,
    widthCollapsed: 72,
  },
  bottomNav: {
    height: 56,
  },
  recordButton: {
    size: {
      sm: 48,
      md: 64,
      lg: 80,
    },
  },
};
