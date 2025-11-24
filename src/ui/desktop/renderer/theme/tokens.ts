/**
 * Design System Tokens
 * Centralized design values for the ORCHIDEA RTSTT application
 */

// Color Palette - Professional & Accessible (WCAG AA Compliant)
export const colors = {
  // Primary colors - Modern Blue
  primary: {
    main: '#0066CC',      // Deep professional blue
    dark: '#004C99',      // Darker blue for contrast
    light: '#3385DB',     // Lighter blue for hover states
    lighter: '#66A3E0',   // Very light blue for backgrounds
    contrast: '#FFFFFF',  // White text for good contrast
  },
  // Secondary colors - Elegant Purple
  secondary: {
    main: '#7C3AED',      // Rich purple
    dark: '#5B21B6',      // Deep purple
    light: '#A78BFA',     // Light purple
    contrast: '#FFFFFF',  // White text
  },
  // Semantic colors
  success: {
    main: '#059669',      // Modern green (better than Material default)
    dark: '#047857',      // Dark green
    light: '#10B981',     // Light green
  },
  warning: {
    main: '#F59E0B',      // Amber warning
    dark: '#D97706',      // Dark amber
    light: '#FBBF24',     // Light amber
  },
  error: {
    main: '#DC2626',      // Modern red
    dark: '#B91C1C',      // Dark red
    light: '#EF4444',     // Light red
  },
  info: {
    main: '#0EA5E9',      // Sky blue
    dark: '#0284C7',      // Dark sky blue
    light: '#38BDF8',     // Light sky blue
  },
  // Light theme - Clean & Modern
  light: {
    background: '#F8FAFC',    // Slightly blue-tinted white
    surface: '#FFFFFF',       // Pure white for cards
    textPrimary: '#0F172A',   // Near-black with blue tint
    textSecondary: '#64748B', // Medium gray-blue
    border: '#E2E8F0',        // Light gray-blue
    divider: '#F1F5F9',       // Very light gray-blue
  },
  // Dark theme - Rich & Professional
  dark: {
    background: '#0F172A',    // Deep navy blue
    surface: '#1E293B',       // Lighter navy for cards
    textPrimary: '#F8FAFC',   // Off-white for readability
    textSecondary: '#94A3B8', // Medium gray-blue
    border: '#334155',        // Visible dark border
    divider: '#1E293B',       // Subtle divider
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
