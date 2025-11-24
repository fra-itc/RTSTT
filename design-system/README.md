# 🎨 Frisco Whisper RTX - Design System

Complete branding and UI design system for the Frisco Whisper RTX application.

## 📦 What's Included

```
design-system/
├── tokens/          # Design tokens (colors, typography, spacing)
├── styles/          # SCSS variables, mixins, animations
├── components/      # Component styles (buttons, cards, badges)
├── assets/          # Brand assets (logos, icons)
├── docs/            # Documentation and guidelines
└── tailwind.config.js  # Tailwind CSS configuration
```

## 🚀 Quick Start

### Using SCSS

```scss
// Import the design system
@import 'design-system/styles/variables';
@import 'design-system/styles/mixins';
@import 'design-system/styles/animations';

// Use variables
.my-button {
  background: $neon-green;
  color: $bg-primary;
  padding: $space-4;
  border-radius: $radius-base;
}

// Use mixins
.my-card {
  @include card;
  @include neon-glow;
}
```

### Using Tailwind CSS

```javascript
// tailwind.config.js
const friscoRTX = require('./design-system/tailwind.config.js');

module.exports = {
  ...friscoRTX,
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    ...friscoRTX.content,
  ],
};
```

```html
<!-- Use Tailwind classes -->
<button class="bg-neon-500 text-dark-300 px-6 py-3 rounded-lg shadow-glow hover:shadow-glow-lg">
  Primary Button
</button>

<div class="glass rounded-xl p-6">
  <h2 class="text-gradient-rtx text-2xl font-display">Glassmorphism Card</h2>
</div>
```

## 🌈 Color Palette

### Primary Brand

- **Neon Green** (`#00FF41`) - Primary brand color, RTX signature
- **Neon Green Glow** (`#00FF4180`) - 50% opacity for glows
- **Neon Green Dark** (`#00CC33`) - Hover states
- **Neon Green Light** (`#33FF66`) - Highlights

### Backgrounds

- **Primary** (`#1A1D2E`) - Main application background
- **Secondary** (`#242838`) - Cards and containers
- **Tertiary** (`#2E3244`) - Elevated surfaces
- **Quaternary** (`#383C52`) - Hover states
- **Overlay** (`#0F111A`) - Modal backdrops

### Status Colors

- **Success** (`#00FF41`) - Completed operations
- **Processing** (`#00D4FF`) - Active transcriptions
- **Pending** (`#FFB800`) - Queued jobs
- **Error** (`#FF3366`) - Failed operations
- **Warning** (`#FFD700`) - Attention needed

### Accent Colors

- **NVIDIA Green** (`#76B900`) - NVIDIA branding
- **RTX Cyan** (`#00E5FF`) - RTX accent
- **AI Purple** (`#8B5CF6`) - AI/ML operations
- **Premium Gold** (`#FFD700`) - Premium features

## 🎯 Typography

### Font Families

- **Primary**: Inter - Clean, modern UI font
- **Mono**: JetBrains Mono - Code, logs, technical data
- **Display**: Orbitron - Headers, tech aesthetic

### Font Sizes

```scss
$text-xs: 0.75rem;   // 12px - Captions
$text-sm: 0.875rem;  // 14px - Secondary text
$text-base: 1rem;    // 16px - Body text
$text-lg: 1.125rem;  // 18px - Large body
$text-xl: 1.25rem;   // 20px - Subheadings
$text-2xl: 1.5rem;   // 24px - Section headers
$text-3xl: 2rem;     // 32px - Page headers
$text-4xl: 2.5rem;   // 40px - Hero text
$text-5xl: 3rem;     // 48px - Display text
```

## 🎨 Component Examples

### Buttons

```html
<!-- Primary Button -->
<button class="btn-primary">
  <svg><!-- Icon --></svg>
  Process Audio
</button>

<!-- Secondary Button -->
<button class="btn-secondary">
  View Details
</button>

<!-- Ghost Button -->
<button class="btn-ghost">
  Cancel
</button>

<!-- Gradient Button -->
<button class="btn-gradient">
  Start Transcription
</button>
```

### Cards

```html
<!-- Standard Card -->
<div class="card">
  <div class="card-header">
    <h3>Job Status</h3>
    <span class="badge-processing">Processing</span>
  </div>
  <div class="card-body">
    <p>Transcribing audio with Whisper large-v3 model...</p>
  </div>
  <div class="card-footer">
    <button class="btn-ghost">View Log</button>
    <button class="btn-primary">Download</button>
  </div>
</div>

<!-- Glass Card with Glow -->
<div class="card-glass card-glow">
  <h2 class="text-gradient-rtx font-display">RTX Accelerated</h2>
  <p class="text-secondary">NVIDIA GeForce RTX 5080</p>
</div>

<!-- Processing Card (Animated) -->
<div class="card-processing">
  <div class="flex items-center gap-4">
    <div class="badge-processing">Active</div>
    <span class="font-mono text-sm">model: large-v3</span>
  </div>
  <div class="progress-bar mt-4">
    <div class="progress-fill" style="width: 65%"></div>
  </div>
</div>
```

### Badges

```html
<!-- Status Badges -->
<span class="badge-success">Completed</span>
<span class="badge-processing">Processing</span>
<span class="badge-pending">Queued</span>
<span class="badge-error">Failed</span>

<!-- Solid Variants -->
<span class="badge-success badge-solid">Success</span>
<span class="badge-nvidia badge-solid">NVIDIA RTX</span>

<!-- Badge with Icon -->
<span class="badge-rtx">
  <svg><!-- GPU icon --></svg>
  RTX 5080
</span>
```

## ✨ Special Effects

### Neon Glow

```scss
// SCSS
.element {
  @include neon-glow($neon-green, 1);
}

// Tailwind
<div class="shadow-glow hover:shadow-glow-lg">
  Glowing Element
</div>
```

### Glassmorphism

```scss
// SCSS
.glass-panel {
  @include glass($blur-base, 0.03, 0.1);
}

// Tailwind
<div class="glass rounded-xl backdrop-blur-md">
  Glass Effect
</div>
```

### Gradient Text

```scss
// SCSS
.title {
  @include gradient-text($gradient-rtx);
}

// Tailwind
<h1 class="text-gradient-rtx text-4xl font-display">
  Frisco Whisper RTX
</h1>
```

### Animations

```scss
// SCSS
.processing {
  @include pulse-animation(2s);
}

.glow-effect {
  @include glow-animation(2s);
}

// Tailwind
<div class="animate-pulse-slow">Pulsing</div>
<div class="animate-glow">Glowing</div>
<div class="animate-scan">Scanning</div>
```

## 📐 Spacing Scale

```scss
$space-0:   0;
$space-1:   0.25rem;   // 4px
$space-2:   0.5rem;    // 8px
$space-3:   0.75rem;   // 12px
$space-4:   1rem;      // 16px
$space-5:   1.25rem;   // 20px
$space-6:   1.5rem;    // 24px
$space-8:   2rem;      // 32px
$space-10:  2.5rem;    // 40px
$space-12:  3rem;      // 48px
$space-16:  4rem;      // 64px
$space-20:  5rem;      // 80px
$space-24:  6rem;      // 96px
```

## 🎯 Usage Guidelines

### When to Use Neon Green

✅ **Do:**
- Primary CTAs (Call to Action)
- Success states
- Active/selected states
- Focus indicators
- Brand elements

❌ **Don't:**
- Overwhelming backgrounds
- Large text blocks
- Disabled states
- Error messages

### When to Use Glow Effects

✅ **Do:**
- Hover states on interactive elements
- Status indicators (processing, active)
- Hero elements
- Special features highlight

❌ **Don't:**
- Static content
- Body text
- Frequently recurring elements (avoid fatigue)

### Dark Mode Principles

1. **Contrast**: Minimum 7:1 ratio for text
2. **Elevation**: Use lighter backgrounds for elevated surfaces
3. **Glow**: Neon accents provide depth without harsh shadows
4. **Blur**: Glassmorphism adds sophistication

## 🔧 Development

### Prerequisites

```bash
# Install required fonts
# Inter: https://fonts.google.com/specimen/Inter
# JetBrains Mono: https://www.jetbrains.com/lp/mono/
# Orbitron: https://fonts.google.com/specimen/Orbitron
```

### Build Process

```bash
# Compile SCSS
npm run build:scss

# Generate Tailwind CSS
npm run build:tailwind

# Build all
npm run build:design-system
```

## 📚 Resources

- [Design Tokens](./tokens/) - JSON design tokens
- [SCSS Variables](./styles/_variables.scss) - All SCSS variables
- [SCSS Mixins](./styles/_mixins.scss) - Reusable mixins
- [Animations](./styles/_animations.scss) - Keyframe animations
- [Tailwind Config](./tailwind.config.js) - Tailwind integration
- [Brand Guidelines](./docs/BRAND_GUIDELINES.md) - Complete brand guide

## 🤝 Contributing

When adding new components or tokens:

1. Follow naming conventions (`$prefix-name`)
2. Document all new variables
3. Add usage examples
4. Test in both light and dark modes
5. Ensure WCAG AA compliance

## 📄 License

Part of the Frisco Whisper RTX project.

---

**Version**: 1.0.0
**Last Updated**: 2024-11-24
**Maintained by**: Frisco RTX Team
