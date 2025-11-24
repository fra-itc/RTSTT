/**
 * Frisco Whisper RTX - Tailwind CSS Configuration
 * Complete design system integration with Tailwind
 *
 * Usage:
 * - Import this config in your main tailwind.config.js
 * - Or use directly: npx tailwindcss -c design-system/tailwind.config.js
 */

module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx,html}',
    './design-system/**/*.{js,jsx,ts,tsx,html}',
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      // ============================================
      // COLORS
      // ============================================
      colors: {
        // Neon Green - Primary Brand
        'neon': {
          50: '#E6FFF0',
          100: '#CCFFE1',
          200: '#99FFC3',
          300: '#66FFA5',
          400: '#33FF87',
          500: '#00FF41',  // Primary
          600: '#00CC33',
          700: '#009926',
          800: '#006619',
          900: '#00330D'
        },
        // Dark Backgrounds
        'dark': {
          50: '#383C52',
          100: '#2E3244',
          200: '#242838',
          300: '#1A1D2E',  // Primary BG
          400: '#15182A',
          500: '#0F111A',  // Overlay
        },
        // Status Colors
        'status': {
          success: '#00FF41',
          processing: '#00D4FF',
          pending: '#FFB800',
          error: '#FF3366',
          warning: '#FFD700',
        },
        // RTX Accents
        'rtx': {
          'cyan': '#00E5FF',
          'purple': '#8B5CF6',
          'nvidia': '#76B900',
          'gold': '#FFD700',
        }
      },

      // ============================================
      // TYPOGRAPHY
      // ============================================
      fontFamily: {
        'primary': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Cascadia Code', 'Consolas', 'monospace'],
        'display': ['Orbitron', 'Russo One', 'sans-serif'],
      },

      fontSize: {
        'xs': '0.75rem',    // 12px
        'sm': '0.875rem',   // 14px
        'base': '1rem',     // 16px
        'lg': '1.125rem',   // 18px
        'xl': '1.25rem',    // 20px
        '2xl': '1.5rem',    // 24px
        '3xl': '2rem',      // 32px
        '4xl': '2.5rem',    // 40px
        '5xl': '3rem',      // 48px
      },

      // ============================================
      // SPACING
      // ============================================
      spacing: {
        '0': '0',
        '1': '0.25rem',   // 4px
        '2': '0.5rem',    // 8px
        '3': '0.75rem',   // 12px
        '4': '1rem',      // 16px
        '5': '1.25rem',   // 20px
        '6': '1.5rem',    // 24px
        '8': '2rem',      // 32px
        '10': '2.5rem',   // 40px
        '12': '3rem',     // 48px
        '16': '4rem',     // 64px
        '20': '5rem',     // 80px
        '24': '6rem',     // 96px
      },

      // ============================================
      // ANIMATIONS
      // ============================================
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite',
        'scan': 'scan-line 4s linear infinite',
        'spin-slow': 'spin 2s linear infinite',
        'bounce-slow': 'bounce 3s infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'shimmer': 'shimmer 2s linear infinite',
      },

      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(0, 255, 65, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(0, 255, 65, 0.8), 0 0 30px rgba(0, 255, 65, 0.4)' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(-100%)', opacity: '0.8' },
          '50%': { opacity: '1' },
          '100%': { transform: 'translateY(100%)', opacity: '0.8' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },

      // ============================================
      // BOX SHADOWS
      // ============================================
      boxShadow: {
        'glow': '0 0 20px rgba(0, 255, 65, 0.5)',
        'glow-lg': '0 0 40px rgba(0, 255, 65, 0.6)',
        'glow-xl': '0 0 60px rgba(0, 255, 65, 0.8)',
        'inner-glow': 'inset 0 0 20px rgba(0, 255, 65, 0.1)',
        'neon-text': '0 0 10px rgba(0, 255, 65, 0.8), 0 0 20px rgba(0, 255, 65, 0.6), 0 0 30px rgba(0, 255, 65, 0.4)',
      },

      // ============================================
      // BORDER RADIUS
      // ============================================
      borderRadius: {
        'none': '0',
        'sm': '0.25rem',   // 4px
        'DEFAULT': '0.5rem',    // 8px
        'md': '0.75rem',   // 12px
        'lg': '1rem',      // 16px
        'xl': '1.25rem',   // 20px
        '2xl': '1.5rem',   // 24px
        'full': '9999px',
      },

      // ============================================
      // BACKDROP BLUR
      // ============================================
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'DEFAULT': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
      },

      // ============================================
      // BACKGROUND IMAGES
      // ============================================
      backgroundImage: {
        'gradient-rtx': 'linear-gradient(135deg, #00FF41 0%, #00D4FF 100%)',
        'gradient-nvidia': 'linear-gradient(135deg, #76B900 0%, #00FF41 100%)',
        'gradient-purple': 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
        'gradient-gold': 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
        'shimmer': 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
      },

      // ============================================
      // TRANSITIONS
      // ============================================
      transitionDuration: {
        'fast': '150ms',
        'DEFAULT': '250ms',
        'slow': '350ms',
        'slower': '500ms',
      },

      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
    },
  },
  plugins: [
    // Custom plugin for text gradients
    function({ addUtilities }) {
      const newUtilities = {
        '.text-gradient-rtx': {
          background: 'linear-gradient(135deg, #00FF41 0%, #00D4FF 100%)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text',
        },
        '.text-gradient-nvidia': {
          background: 'linear-gradient(135deg, #76B900 0%, #00FF41 100%)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text',
        },
        '.glass': {
          background: 'rgba(255, 255, 255, 0.03)',
          'backdrop-filter': 'blur(8px)',
          '-webkit-backdrop-filter': 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        },
        '.glass-dark': {
          background: 'rgba(0, 0, 0, 0.05)',
          'backdrop-filter': 'blur(8px)',
          '-webkit-backdrop-filter': 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
        },
      };
      addUtilities(newUtilities);
    },
  ],
};
