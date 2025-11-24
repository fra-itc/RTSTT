# Parallel Frontend Development Plan with TDD

## Executive Summary
Parallel development strategy to build modern UI components with test-driven development, maximizing efficiency through independent parallel tracks, then sync phase for integration.

## What We Have (Analysis)

### ✅ Working Backend (feature/track3-frontend-integration)
- **Audio Pipeline**: Microphone → WebSocket → Backend → STT → Transcriptions ✓
- **Proven Transcription**: Italian, French, English auto-detection working
- **WebSocket Gateway**: Stable connection, handles audio chunks properly
- **Backend Services**: STT (working), NLP (stub), Summary (stub)

### ✅ UI Foundation (feature/modern-ux-redesign)
- **Design System**: Complete tokens (colors, spacing, typography, shadows)
- **Theme System**: Dark/Light mode with persistence
- **AppShell Layout**: Responsive layout with sidebar/drawer
- **MUI Integration**: Theme provider, component overrides

### ❌ Missing Components
1. **AudioControlPanel** - Mic selection, volume, preamp, waveform, record button
2. **RecordButton** - Large, animated record button with states
3. **WaveformVisualizer** - Real-time canvas-based audio visualization
4. **TranscriptionCard** - Display transcription with confidence, timestamp, latency
5. **TranscriptionList** - Virtualized list of transcription cards
6. **StatusBar** - Connection status, processing state, notifications
7. **Integration Layer** - Connect UI components to working audio backend

## TDD Strategy

### Why TDD?
- ✅ **Parallel Development**: Each track can write tests independently
- ✅ **Clear Contracts**: Tests define component interfaces upfront
- ✅ **Regression Prevention**: Catch breaks early during integration
- ✅ **Living Documentation**: Tests show how components should be used
- ✅ **Confidence**: Know integration will work before we start

### Testing Stack
```json
{
  "testing": {
    "unit": "vitest + @testing-library/react",
    "component": "@testing-library/react + @testing-library/user-event",
    "integration": "vitest + msw (mock service worker)",
    "e2e": "playwright (later phase)"
  }
}
```

### Test-First Workflow
```
For each component:
1. Write test describing behavior
2. Run test (watch it fail - RED)
3. Write minimal code to pass (GREEN)
4. Refactor for quality (REFACTOR)
5. Repeat for next behavior
```

## Parallel Development Tracks

### 🎯 Track A: RecordButton Component
**Developer A / Time: 2-3 hours**

**Phase 1: Write Tests First**
```typescript
// RecordButton.test.tsx
describe('RecordButton', () => {
  it('renders idle state with microphone icon')
  it('shows recording state when recording prop is true')
  it('displays timer when recording')
  it('calls onClick when clicked')
  it('is disabled when disabled prop is true')
  it('shows pulse animation when recording')
  it('has proper ARIA labels for accessibility')
  it('supports keyboard interaction (Enter/Space)')
})
```

**Phase 2: Implement Component**
- Idle: Blue circle with mic icon
- Recording: Red circle, pulsing, with timer
- Disabled: Gray, 50% opacity
- Variants: small (48px), medium (64px), large (80px)
- Accessibility: ARIA labels, keyboard support

**Deliverables:**
- `components/RecordButton/RecordButton.tsx`
- `components/RecordButton/RecordButton.test.tsx`
- `components/RecordButton/index.ts`

---

### 🎯 Track B: WaveformVisualizer Component
**Developer B / Time: 3-4 hours**

**Phase 1: Write Tests First**
```typescript
// WaveformVisualizer.test.tsx
describe('WaveformVisualizer', () => {
  it('renders canvas element with correct dimensions')
  it('draws waveform from audio data array')
  it('shows VAD threshold line when enabled')
  it('highlights active speech regions')
  it('updates in real-time with new audio data')
  it('is responsive to container width')
  it('shows empty state when no audio data')
  it('has proper ARIA labels')
})
```

**Phase 2: Implement Component**
- Canvas-based rendering (requestAnimationFrame)
- Real-time audio data visualization
- VAD threshold indicator
- Active speech highlighting
- Responsive width (100% of container)
- Color variants (primary, success, warning, error)

**Technical:**
- Use `useRef` for canvas element
- `useEffect` for animation loop
- Debounced resize handler
- Clean up animation frame on unmount

**Deliverables:**
- `components/WaveformVisualizer/WaveformVisualizer.tsx`
- `components/WaveformVisualizer/WaveformVisualizer.test.tsx`
- `components/WaveformVisualizer/index.ts`

---

### 🎯 Track C: TranscriptionCard Component
**Developer C / Time: 2-3 hours**

**Phase 1: Write Tests First**
```typescript
// TranscriptionCard.test.tsx
describe('TranscriptionCard', () => {
  it('renders transcription text')
  it('shows confidence badge with color coding')
  it('displays formatted timestamp')
  it('shows latency metric')
  it('shows copy button on hover')
  it('calls onCopy with text when copy clicked')
  it('supports inline editing when onEdit provided')
  it('has proper confidence color (green>0.8, yellow>0.5, red)')
  it('is accessible with keyboard navigation')
})
```

**Phase 2: Implement Component**
- Card with hover effects
- Confidence badge (color-coded: green ≥0.8, yellow ≥0.5, red <0.5)
- Timestamp formatting (relative time)
- Latency display (ms)
- Copy button (appears on hover)
- Optional inline edit capability

**Deliverables:**
- `components/TranscriptionCard/TranscriptionCard.tsx`
- `components/TranscriptionCard/TranscriptionCard.test.tsx`
- `components/TranscriptionCard/index.ts`

---

### 🎯 Track D: AudioControlPanel Component
**Developer D / Time: 4-5 hours**

**Phase 1: Write Tests First**
```typescript
// AudioControlPanel.test.tsx
describe('AudioControlPanel', () => {
  it('renders device selector with loaded devices')
  it('shows volume slider with current value')
  it('shows preamp gain slider')
  it('displays waveform visualization')
  it('includes record button')
  it('shows language selector')
  it('shows model selector')
  it('has collapsible advanced settings section')
  it('calls onDeviceChange when device selected')
  it('calls onVolumeChange when volume adjusted')
  it('calls onRecordToggle when record button clicked')
})
```

**Phase 2: Implement Component**
- Device selector dropdown (with refresh button)
- Volume slider (0-100%)
- Preamp gain slider (-12dB to +12dB)
- Embedded WaveformVisualizer
- Large RecordButton
- Language selector (chips or dropdown)
- Model selector
- Advanced settings accordion (sample rate, channels, VAD)
- Responsive layout (sidebar → card → sheet)

**Integration Points:**
- Uses RecordButton from Track A
- Uses WaveformVisualizer from Track B
- Mock these components in tests

**Deliverables:**
- `components/AudioControlPanel/AudioControlPanel.tsx`
- `components/AudioControlPanel/AudioControlPanel.test.tsx`
- `components/AudioControlPanel/index.ts`

---

### 🎯 Track E: TranscriptionList Component
**Developer E / Time: 2-3 hours**

**Phase 1: Write Tests First**
```typescript
// TranscriptionList.test.tsx
describe('TranscriptionList', () => {
  it('renders list of transcription cards')
  it('shows empty state when no transcriptions')
  it('supports virtualized scrolling for performance')
  it('has search/filter capability')
  it('shows export button')
  it('calls onExport with selected format')
  it('auto-scrolls to newest transcription')
  it('supports keyboard navigation')
})
```

**Phase 2: Implement Component**
- List container with TranscriptionCard components
- Empty state with instructions
- Search/filter bar
- Export dropdown (TXT, JSON, SRT)
- Auto-scroll to bottom option
- Virtualized scrolling (react-window)

**Integration Points:**
- Uses TranscriptionCard from Track C
- Mock in tests

**Deliverables:**
- `components/TranscriptionList/TranscriptionList.tsx`
- `components/TranscriptionList/TranscriptionList.test.tsx`
- `components/TranscriptionList/index.ts`

---

## Sync Phase: Integration

### Integration Tasks (Sequential)
**Time: 3-4 hours**

#### 1. Component Integration Testing
```typescript
// integration.test.tsx
describe('Component Integration', () => {
  it('AudioControlPanel integrates RecordButton and WaveformVisualizer')
  it('TranscriptionList integrates TranscriptionCard')
  it('All components respect theme (light/dark)')
  it('All components are responsive at different breakpoints')
})
```

#### 2. Backend Integration
**Connect to working audio pipeline from feature/track3-frontend-integration**

Create integration layer:
```typescript
// hooks/useAudioPipeline.ts
export const useAudioPipeline = () => {
  // WebSocket connection (from working branch)
  // Audio capture (from working branch)
  // State management
  return {
    devices,
    selectedDevice,
    isRecording,
    isConnected,
    transcriptions,
    audioLevel,
    waveformData,
    handleRecordToggle,
    handleDeviceChange,
    // ...all handlers
  }
}
```

#### 3. Wire Components to Backend
```typescript
// views/MainView.tsx
const MainView = () => {
  const audio = useAudioPipeline();

  return (
    <AppShell
      sidebar={
        <AudioControlPanel
          devices={audio.devices}
          selectedDevice={audio.selectedDevice}
          isRecording={audio.isRecording}
          audioLevel={audio.audioLevel}
          waveformData={audio.waveformData}
          onRecordToggle={audio.handleRecordToggle}
          onDeviceChange={audio.handleDeviceChange}
        />
      }
    >
      <TranscriptionList
        transcriptions={audio.transcriptions}
        onExport={audio.handleExport}
      />
    </AppShell>
  );
};
```

#### 4. Integration Testing with Real Backend
- Start backend containers
- Test microphone access
- Test WebSocket connection
- Test recording → transcription flow
- Test all UI controls
- Test theme switching
- Test responsive breakpoints

---

## Testing Setup

### Install Testing Dependencies
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### Vitest Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

### Test Setup File
```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

---

## Execution Timeline

### Day 1: Setup + Parallel Development
**Morning (2 hours):**
- [x] Install testing dependencies ✓
- [x] Configure Vitest ✓
- [x] Create test setup files ✓
- [ ] Create test templates for all tracks

**Afternoon (4 hours):**
- [ ] Track A, B, C, D, E work in parallel
- [ ] Each track: Write tests → Implement → Pass tests
- [ ] Code reviews as tracks complete

**Evening (2 hours):**
- [ ] All tracks should have passing tests
- [ ] Component demos in Storybook (optional)

### Day 2: Integration + Testing
**Morning (3 hours):**
- [ ] Create useAudioPipeline integration hook
- [ ] Wire AudioControlPanel to backend
- [ ] Wire TranscriptionList to backend
- [ ] Integration tests

**Afternoon (3 hours):**
- [ ] Full system testing with real audio
- [ ] Test all user workflows
- [ ] Fix any integration bugs
- [ ] Responsive testing (mobile, tablet, desktop)

**Evening (2 hours):**
- [ ] Theme testing (light/dark)
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Final QA

---

## Success Criteria

### Component Quality
- ✅ All unit tests passing (>90% coverage)
- ✅ All integration tests passing
- ✅ Components work in isolation
- ✅ Components integrate properly
- ✅ Responsive at all breakpoints
- ✅ Accessible (ARIA, keyboard nav)
- ✅ Theme support (light/dark)

### Backend Integration
- ✅ Microphone access working
- ✅ WebSocket connection stable
- ✅ Audio chunks streaming
- ✅ Transcriptions displaying in real-time
- ✅ All controls functional
- ✅ Error handling graceful

### User Experience
- ✅ Smooth animations
- ✅ Intuitive workflows
- ✅ Fast performance (60fps)
- ✅ Clear visual feedback
- ✅ Professional appearance

---

## Improvements from Current State

### 1. **TDD Approach**
- **Before**: Write code → hope it works → debug
- **After**: Define behavior → write test → implement → verify

### 2. **Parallel Development**
- **Before**: Sequential component building (slow)
- **After**: 5 developers work simultaneously (fast)

### 3. **Integration Strategy**
- **Before**: Big bang integration at the end
- **After**: Planned sync phase with integration tests

### 4. **Component Contracts**
- **Before**: Unclear interfaces between components
- **After**: Tests define clear contracts upfront

### 5. **Quality Assurance**
- **Before**: Manual testing only
- **After**: Automated tests + manual QA

### 6. **Confidence**
- **Before**: Uncertain if integration will work
- **After**: Tests prove integration before we start

---

## Risk Mitigation

### Technical Risks
| Risk | Mitigation |
|------|-----------|
| Components don't integrate | Write integration tests in sync phase |
| WebSocket backend different | Extract working code to useAudioPipeline hook |
| Performance issues | Use React.memo, useMemo, virtualization |
| Theme bugs | Test both themes in all tests |
| Responsive issues | Test at all breakpoints |

### Process Risks
| Risk | Mitigation |
|------|-----------|
| Tracks get blocked | Keep tracks independent, mock dependencies |
| Tests take too long | Focus on key behaviors, not 100% coverage |
| Integration phase overruns | Have clear integration checklist |
| Backend changes | Version backend API, use mocks in tests |

---

## Next Steps

### Immediate Actions
1. Install testing dependencies
2. Configure Vitest
3. Create test setup files
4. Assign tracks to developers (or work sequentially)
5. Start Track A (RecordButton) - smallest component

### Recommended Order (if working solo)
1. **RecordButton** (easiest, fast win)
2. **WaveformVisualizer** (complex but independent)
3. **TranscriptionCard** (simple, quick)
4. **TranscriptionList** (uses TranscriptionCard)
5. **AudioControlPanel** (uses RecordButton + WaveformVisualizer)
6. **Integration Phase**

---

**Document Version**: 1.0
**Created**: 2025-11-24
**Status**: Ready for Execution
