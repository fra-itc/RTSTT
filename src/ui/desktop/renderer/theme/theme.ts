/**
 * MUI Theme Configuration
 * Applies design tokens to Material-UI theme
 */

import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';
import { colors, typography, spacing, borderRadius, elevation, breakpoints, transitions, components } from './tokens';

// Common theme options shared between light and dark themes
const commonOptions: ThemeOptions = {
  breakpoints: {
    values: breakpoints,
  },
  typography: {
    fontFamily: typography.fontFamily.base,
    fontSize: 14,
    h1: {
      fontSize: typography.fontSize['3xl'],
      fontWeight: typography.fontWeight.bold,
      lineHeight: typography.lineHeight.tight,
    },
    h2: {
      fontSize: typography.fontSize['2xl'],
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.tight,
    },
    h3: {
      fontSize: typography.fontSize.xl,
      fontWeight: typography.fontWeight.semibold,
      lineHeight: typography.lineHeight.normal,
    },
    h4: {
      fontSize: typography.fontSize.lg,
      fontWeight: typography.fontWeight.medium,
      lineHeight: typography.lineHeight.normal,
    },
    body1: {
      fontSize: typography.fontSize.base,
      lineHeight: typography.lineHeight.normal,
    },
    body2: {
      fontSize: typography.fontSize.sm,
      lineHeight: typography.lineHeight.normal,
    },
    caption: {
      fontSize: typography.fontSize.xs,
      lineHeight: typography.lineHeight.normal,
    },
  },
  shape: {
    borderRadius: borderRadius.md,
  },
  spacing: spacing.sm, // Base spacing unit
  transitions: {
    duration: transitions.duration,
    easing: transitions.easing,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: typography.fontWeight.medium,
          borderRadius: borderRadius.md,
          transition: `all ${transitions.duration.short}ms ${transitions.easing.easeInOut}`,
        },
        sizeLarge: {
          padding: `${spacing.md}px ${spacing.lg}px`,
          fontSize: typography.fontSize.base,
        },
        sizeMedium: {
          padding: `${spacing.sm}px ${spacing.md}px`,
          fontSize: typography.fontSize.sm,
        },
        sizeSmall: {
          padding: `${spacing.xs}px ${spacing.sm}px`,
          fontSize: typography.fontSize.xs,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.lg,
          boxShadow: elevation[2],
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
        },
        elevation1: {
          boxShadow: elevation[1],
        },
        elevation2: {
          boxShadow: elevation[2],
        },
        elevation3: {
          boxShadow: elevation[3],
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: elevation[2],
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
          transition: `all ${transitions.duration.short}ms ${transitions.easing.easeInOut}`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: borderRadius.md,
          fontWeight: typography.fontWeight.medium,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: borderRadius.md,
          },
        },
      },
    },
  },
};

// Light theme
export const lightTheme = createTheme({
  ...commonOptions,
  palette: {
    mode: 'light',
    primary: {
      main: colors.primary.main,
      dark: colors.primary.dark,
      light: colors.primary.light,
      contrastText: colors.primary.contrast,
    },
    secondary: {
      main: colors.secondary.main,
      dark: colors.secondary.dark,
      light: colors.secondary.light,
      contrastText: colors.secondary.contrast,
    },
    success: {
      main: colors.success.main,
      dark: colors.success.dark,
      light: colors.success.light,
    },
    warning: {
      main: colors.warning.main,
      dark: colors.warning.dark,
      light: colors.warning.light,
    },
    error: {
      main: colors.error.main,
      dark: colors.error.dark,
      light: colors.error.light,
    },
    info: {
      main: colors.info.main,
      dark: colors.info.dark,
      light: colors.info.light,
    },
    background: {
      default: colors.light.background,
      paper: colors.light.surface,
    },
    text: {
      primary: colors.light.textPrimary,
      secondary: colors.light.textSecondary,
    },
    divider: colors.light.divider,
  },
});

// Dark theme
export const darkTheme = createTheme({
  ...commonOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: colors.primary.lighter,
      dark: colors.primary.light,
      light: '#90caf9',
      contrastText: colors.dark.textPrimary,
    },
    secondary: {
      main: colors.secondary.light,
      dark: colors.secondary.main,
      light: '#f48fb1',
      contrastText: colors.dark.textPrimary,
    },
    success: {
      main: colors.success.light,
      dark: colors.success.main,
      light: '#81c784',
    },
    warning: {
      main: colors.warning.light,
      dark: colors.warning.main,
      light: '#ffb74d',
    },
    error: {
      main: colors.error.light,
      dark: colors.error.main,
      light: '#e57373',
    },
    info: {
      main: colors.info.light,
      dark: colors.info.main,
      light: '#4fc3f7',
    },
    background: {
      default: colors.dark.background,
      paper: colors.dark.surface,
    },
    text: {
      primary: colors.dark.textPrimary,
      secondary: colors.dark.textSecondary,
    },
    divider: colors.dark.divider,
  },
});

// Type augmentation for custom theme properties
declare module '@mui/material/styles' {
  interface Theme {
    custom: {
      elevation: typeof elevation;
      borderRadius: typeof borderRadius;
      components: typeof components;
    };
  }
  interface ThemeOptions {
    custom?: {
      elevation?: typeof elevation;
      borderRadius?: typeof borderRadius;
      components?: typeof components;
    };
  }
}

// Add custom properties to both themes
[lightTheme, darkTheme].forEach((theme) => {
  theme.custom = {
    elevation,
    borderRadius,
    components,
  };
});

export { lightTheme as default };
