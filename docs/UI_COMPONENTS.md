# UI Components Documentation

This document provides detailed information about all UI components in the ORCHIDEA RTSTT frontend application.

## Table of Contents

- [Overview](#overview)
- [Layout Components](#layout-components)
- [Panel Components](#panel-components)
- [Control Components](#control-components)
- [Visualization Components](#visualization-components)
- [UI Primitives](#ui-primitives)
- [Hooks](#hooks)
- [Theme System](#theme-system)

---

## Overview

The RTSTT frontend is built with:
- **React 18** with TypeScript for type safety
- **Material-UI v7** for consistent, accessible UI components
- **Electron** for cross-platform desktop deployment
- **Web Audio API** for real-time audio processing
- **WebSocket** for real-time backend communication

---

## Layout Components

### AppShell

**Location:** `src/ui/desktop/renderer/components/layout/AppShell.tsx`

Main application shell that provides the overall layout structure.

**Props:**
```typescript
interface AppShellProps {
  title: string;           // Application title
  sidebar?: React.ReactNode;  // Optional sidebar content
  children: React.ReactNode;  // Main content area
}
```

**Features:**
- Responsive sidebar that collapses on smaller screens
- Sticky header with application title
- Flexible content area
- Material-UI theming support

**Usage:**
```tsx
<AppShell title="ORCHIDEA RTSTT" sidebar={<AudioControlPanel {...props} />}>
  <MainView />
</AppShell>
```

---

## Panel Components

### InsightsPanel

**Location:** `src/ui/desktop/renderer/components/InsightsPanel/InsightsPanel.tsx`

Displays real-time NLP insights including keywords, named entities, and sentiment analysis.

**Props:**
```typescript
interface InsightsPanelProps {
  keywords?: Keyword[];        // Extracted keywords with scores
  entities?: NamedEntity[];    // Named entities with types
  sentiment?: Sentiment;       // Sentiment analysis results
  isLoading?: boolean;        // Loading state
  isEmpty?: boolean;          // Empty state
}

interface Keyword {
  keyword: string;  // Keyword text
  score: number;    // Relevance score (0-1)
}

interface NamedEntity {
  text: string;       // Entity text
  type: string;       // Entity type (PERSON, ORG, LOC, DATE, MISC)
  confidence?: number;  // Optional confidence score
}

interface Sentiment {
  label: string;       // Sentiment label (Positive, Negative, Neutral)
  score: number;       // Confidence score (0-1)
  positive?: number;   // Positive sentiment score
  neutral?: number;    // Neutral sentiment score
  negative?: number;   // Negative sentiment score
}
```

**Features:**
- **Keywords Section**
  - Chips with keyword text
  - Opacity based on relevance score
  - Outlined style with primary color
- **Named Entities Section**
  - Color-coded by entity type:
    - Blue (primary): PERSON/PER
    - Purple (secondary): ORG/ORGANIZATION
    - Sky blue (info): LOC/LOCATION/GPE
    - Amber (warning): DATE/TIME
    - Red (error): MISC/MISCELLANEOUS
  - Displays entity type in parentheses
- **Sentiment Analysis Section**
  - Icon based on sentiment (positive/negative/neutral)
  - Confidence score display
  - Optional breakdown visualization with progress bars
- **Loading States:** Skeleton loaders for each section
- **Empty States:** Informative message with icon when no data

**Usage:**
```tsx
<InsightsPanel
  keywords={[
    { keyword: 'machine learning', score: 0.95 },
    { keyword: 'artificial intelligence', score: 0.87 }
  ]}
  entities={[
    { text: 'John Doe', type: 'PERSON' },
    { text: 'Microsoft', type: 'ORG' }
  ]}
  sentiment={{
    label: 'Positive',
    score: 0.92,
    positive: 0.92,
    neutral: 0.06,
    negative: 0.02
  }}
  isLoading={false}
  isEmpty={false}
/>
```

### SuggestionsPanel

**Location:** `src/ui/desktop/renderer/components/SuggestionsPanel/SuggestionsPanel.tsx`

Displays AI-generated summary and intelligent recommendations based on transcribed content.

**Props:**
```typescript
interface SuggestionsPanelProps {
  summary?: string;         // AI-generated summary
  suggestions?: string[];   // List of recommendations
  isLoading?: boolean;     // Loading state
  isEmpty?: boolean;       // Empty state
}
```

**Features:**
- **Summary Section**
  - Displayed in outlined card with background
  - Copy-to-clipboard button
  - Preserves line breaks with `whiteSpace: 'pre-wrap'`
- **Suggestions Section**
  - Numbered list items (1, 2, 3...)
  - Circular badge with suggestion number
  - Individual copy button for each suggestion
  - Hover effects for better interactivity
- **Copy Functionality**
  - Clipboard API integration
  - Success snackbar notification
  - Shows what was copied (summary/suggestion #)
- **Loading States:** Skeleton loaders
- **Empty States:** Informative message with icon

**Usage:**
```tsx
<SuggestionsPanel
  summary="The conversation focused on implementing machine learning models for natural language processing tasks."
  suggestions={[
    'Consider using pre-trained transformers for better accuracy',
    'Implement proper error handling for edge cases',
    'Add comprehensive unit tests for all components'
  ]}
  isLoading={false}
  isEmpty={false}
/>
```

### TranscriptionList

**Location:** `src/ui/desktop/renderer/components/TranscriptionList/TranscriptionList.tsx`

Displays real-time transcription results with timestamps and confidence scores.

**Props:**
```typescript
interface TranscriptionListProps {
  transcriptions: Transcription[];
  onExport?: (format: 'txt' | 'json' | 'srt', data: Transcription[]) => void;
}

interface Transcription {
  text: string;        // Transcribed text
  confidence: number;  // Confidence score (0-1)
  timestamp: string;   // ISO timestamp
  latency: number;     // Processing latency in ms
}
```

**Features:**
- Real-time scrolling list
- Timestamp display
- Confidence score badges
- Export functionality (TXT, JSON, SRT)
- Auto-scroll to latest transcription
- Empty state when no transcriptions

### AudioControlPanel

**Location:** `src/ui/desktop/renderer/components/AudioControlPanel/AudioControlPanel.tsx`

Control panel for audio recording settings and monitoring.

**Features:**
- Device selection dropdown
- Recording toggle button
- Volume and preamp gain sliders
- Audio level meter
- Waveform visualization
- Connection status indicator
- Language and model selection
- Sample rate and channel configuration

---

## Control Components

### RecordButton

**Location:** `src/ui/desktop/renderer/components/RecordButton/RecordButton.tsx`

Large circular button for starting/stopping recording.

**Props:**
```typescript
interface RecordButtonProps {
  isRecording: boolean;
  onClick: () => void;
  disabled?: boolean;
}
```

**Features:**
- Animated recording indicator (pulsing red circle)
- Size variants (small, medium, large)
- Accessible keyboard navigation
- Visual feedback on hover/press

---

## Visualization Components

### WaveformVisualizer

**Location:** `src/ui/desktop/renderer/components/WaveformVisualizer/WaveformVisualizer.tsx`

Real-time audio waveform visualization using Canvas API.

**Props:**
```typescript
interface WaveformVisualizerProps {
  waveformData: Float32Array;  // Audio samples (-1 to 1)
  width?: number;              // Canvas width
  height?: number;             // Canvas height
  color?: string;              // Waveform color
}
```

**Features:**
- Real-time rendering
- Smooth animation
- Responsive sizing
- Themeable colors

### AudioVisualizer

**Location:** `src/ui/desktop/renderer/components/AudioVisualizer/AudioVisualizer.tsx`

Combined audio level and waveform visualization.

**Features:**
- Audio level meter with VU-style display
- Frequency spectrum visualization
- Peak level indicators
- Clipping warnings

---

## UI Primitives

### Button

**Location:** `src/ui/desktop/renderer/components/ui/Button.tsx`

Custom button component with consistent styling.

**Variants:**
- `contained` - Filled button (default)
- `outlined` - Outlined button
- `text` - Text-only button

**Sizes:**
- `small` - Compact button
- `medium` - Standard button (default)
- `large` - Large button

### Input

**Location:** `src/ui/desktop/renderer/components/ui/Input.tsx`

Custom text input with validation support.

### Select

**Location:** `src/ui/desktop/renderer/components/ui/Select.tsx`

Custom dropdown select component.

### Toggle

**Location:** `src/ui/desktop/renderer/components/ui/Toggle.tsx`

Custom toggle switch component.

### NumberInput

**Location:** `src/ui/desktop/renderer/components/ui/NumberInput.tsx`

Numeric input with increment/decrement buttons.

---

## Hooks

### useAudioPipeline

**Location:** `src/ui/desktop/renderer/hooks/useAudioPipeline.ts`

Main hook for managing audio capture, WebSocket communication, and state management.

**Returns:**
```typescript
interface AudioPipelineState {
  // Device management
  devices: AudioDevice[];
  selectedDevice: string;
  isLoadingDevices: boolean;
  loadDevices: () => Promise<void>;
  setSelectedDevice: (deviceId: string) => void;

  // Recording state
  isRecording: boolean;
  recordingDuration: number;
  handleRecordToggle: () => Promise<void>;

  // WebSocket connection
  isConnected: boolean;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  websocketUrl: string;
  wsError: string | null;
  setWebsocketUrl: (url: string) => void;
  wsConnect: () => void;
  wsDisconnect: () => void;

  // Audio settings
  volume: number;
  isMuted: boolean;
  preampGain: number;
  sampleRate: number;
  channels: number;
  handleVolumeChange: (volume: number) => void;
  handlePreampChange: (gain: number) => void;

  // Model settings
  language: string;
  model: string;
  vadThreshold: number;
  handleLanguageChange: (language: string) => void;
  handleModelChange: (model: string) => void;

  // Real-time data
  audioLevel: number;
  waveformData: Float32Array;
  transcriptions: Transcription[];
  chunksProcessed: number;

  // NLP Insights
  insights: Insights;
  summary: string;
  suggestions: string[];

  // Utilities
  clearTranscriptions: () => void;
}
```

**Features:**
- Web Audio API integration
- Microphone device enumeration
- Real-time audio processing
- WebSocket message handling
- State management for all components
- Automatic cleanup on unmount

**WebSocket Message Types:**
- `transcription_segment` / `transcription` - Transcription results
- `nlp_insights` / `insights` - NLP analysis
- `summary` - AI-generated summary
- `suggestions` - AI recommendations
- `results` / `analysis_complete` - Combined results

### useWebSocket

**Location:** `src/ui/desktop/renderer/hooks/useWebSocket.ts`

Generic WebSocket hook for real-time communication.

### useElectronAPI

**Location:** `src/ui/desktop/renderer/hooks/useElectronAPI.ts`

Hook for accessing Electron IPC APIs.

---

## Theme System

### Design Tokens

**Location:** `src/ui/desktop/renderer/theme/tokens.ts`

Centralized design values used throughout the application.

**Color Palette:**

**Primary Colors (Blue):**
- Main: `#0066CC` - Deep professional blue
- Dark: `#004C99` - Darker blue for contrast
- Light: `#3385DB` - Lighter blue for hover states
- Lighter: `#66A3E0` - Very light blue for backgrounds
- Contrast: `#FFFFFF` - White text

**Secondary Colors (Purple):**
- Main: `#7C3AED` - Rich purple
- Dark: `#5B21B6` - Deep purple
- Light: `#A78BFA` - Light purple
- Contrast: `#FFFFFF` - White text

**Semantic Colors:**
- Success: `#059669` (Modern green)
- Warning: `#F59E0B` (Amber)
- Error: `#DC2626` (Modern red)
- Info: `#0EA5E9` (Sky blue)

**Light Theme:**
- Background: `#F8FAFC` (Blue-tinted white)
- Surface: `#FFFFFF` (Pure white)
- Text Primary: `#0F172A` (Near-black with blue tint)
- Text Secondary: `#64748B` (Medium gray-blue)
- Border: `#E2E8F0` (Light gray-blue)
- Divider: `#F1F5F9` (Very light gray-blue)

**Dark Theme:**
- Background: `#0F172A` (Deep navy blue)
- Surface: `#1E293B` (Lighter navy)
- Text Primary: `#F8FAFC` (Off-white)
- Text Secondary: `#94A3B8` (Medium gray-blue)
- Border: `#334155` (Visible dark border)
- Divider: `#1E293B` (Subtle divider)

**Typography:**
- Font Family: Inter, system-ui
- Mono Font: Fira Code, Consolas
- Font Sizes: xs (12px) to 3xl (32px)
- Font Weights: regular (400) to bold (700)

**Spacing:**
Based on 8px grid system:
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px
- 3xl: 64px

**Border Radius:**
- sm: 4px
- md: 8px (default)
- lg: 12px
- xl: 16px
- 2xl: 24px
- full: 9999px (circular)

**Elevation (Shadows):**
- Level 1: Subtle shadow for slight depth
- Level 2: Standard card shadow
- Level 3: Elevated elements
- Level 4: Modal/dialog shadow
- Level 5: Maximum elevation

### Theme Configuration

**Location:** `src/ui/desktop/renderer/theme/theme.ts`

Material-UI theme configuration applying design tokens.

**Features:**
- Light and dark theme variants
- Consistent component styling
- Typography scale
- Responsive breakpoints
- Custom component overrides

### ThemeProvider

**Location:** `src/ui/desktop/renderer/theme/ThemeProvider.tsx`

React context provider for theme switching.

**Features:**
- Theme persistence in localStorage
- System theme detection
- Dynamic theme switching
- CSS custom properties support

---

## Best Practices

### Component Development

1. **TypeScript First**: Always define prop interfaces
2. **Accessibility**: Use semantic HTML and ARIA attributes
3. **Responsive**: Design mobile-first, enhance for desktop
4. **Performance**: Memoize expensive computations with useMemo/useCallback
5. **Testing**: Write unit tests for all components

### State Management

1. **Local State**: Use useState for component-specific state
2. **Shared State**: Use hooks like useAudioPipeline for cross-component state
3. **Side Effects**: Use useEffect with proper dependencies
4. **Cleanup**: Always cleanup subscriptions, timers, and listeners

### Styling

1. **Material-UI sx Prop**: Preferred for component-specific styles
2. **Theme Values**: Always use theme tokens, never hard-coded values
3. **Responsive**: Use theme breakpoints for responsive design
4. **Dark Mode**: Test all components in both light and dark themes

### Error Handling

1. **Error Boundaries**: Wrap components in error boundaries
2. **Try/Catch**: Handle async errors gracefully
3. **User Feedback**: Show error messages in UI
4. **Logging**: Log errors to console for debugging

---

## Component Testing

### Unit Tests

All components should have corresponding test files:
- `ComponentName.test.tsx` alongside the component
- Test rendering, props, user interactions
- Use React Testing Library

Example:
```typescript
import { render, screen } from '@testing-library/react';
import { InsightsPanel } from './InsightsPanel';

test('renders keywords', () => {
  render(
    <InsightsPanel
      keywords={[{ keyword: 'test', score: 0.9 }]}
      entities={[]}
    />
  );
  expect(screen.getByText('test')).toBeInTheDocument();
});
```

### Integration Tests

Test component interactions and data flow:
- MainView with all panels
- useAudioPipeline with WebSocket
- Theme switching

### E2E Tests

Test complete user workflows:
- Recording session from start to finish
- Viewing insights and exporting transcriptions
- Settings configuration and persistence

---

## Future Enhancements

### Planned Components

- **MetricsPanel**: Real-time performance metrics
- **HistoryPanel**: Session history and replay
- **SettingsDialog**: Advanced configuration options
- **ExportDialog**: Enhanced export options with templates
- **NotificationsPanel**: System notifications and alerts

### Planned Features

- Drag-and-drop panel layout customization
- Keyboard shortcuts for common actions
- Multi-language UI support (i18n)
- Custom theme creation
- Component storybook for documentation

---

## Contributing

When adding new components:

1. Follow the existing component structure
2. Create proper TypeScript interfaces
3. Add comprehensive prop documentation
4. Include examples in this documentation
5. Write unit tests
6. Update the component index exports
7. Consider accessibility from the start

---

## Resources

- [Material-UI Documentation](https://mui.com/material-ui/getting-started/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Electron Documentation](https://www.electronjs.org/docs/latest)

---

**Last Updated**: November 24, 2025
