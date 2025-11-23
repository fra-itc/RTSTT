# Audio Tester Guide

## Overview

The Audio Tester is a comprehensive testing suite integrated into the RTSTT frontend that allows you to test real-time speech recognition with full control over audio input parameters and model settings.

## Features

### 1. Visual Microphone Selection
- **Real-time device enumeration**: Automatically detects all available audio input devices
- **Dropdown selection**: Choose from any connected microphone
- **Device refresh**: Manually refresh the device list without restarting the app
- **Device labels**: Shows full device names for easy identification

### 2. Comprehensive Audio Controls

#### Volume Control
- **Range**: 0-100%
- **Mute button**: Instantly mute/unmute input
- **Real-time adjustment**: Change volume during recording (disabled during active test)

#### Preamp Gain
- **Range**: -20 dB to +20 dB
- **Use case**: Boost weak microphones or reduce overly sensitive ones
- **Granular control**: 1 dB steps for precise adjustment

#### Sample Rate
- **Options**: 8000 Hz, 16000 Hz, 44100 Hz, 48000 Hz
- **Default**: 16000 Hz (optimal for speech recognition)
- **Impact**: Higher rates = better quality but more bandwidth

#### Channels
- **Mono**: Single channel (recommended for speech)
- **Stereo**: Dual channel (for spatial audio)

### 3. Model Configuration

#### Language Selection
Supported languages:
- English (US) - `en-US`
- English (UK) - `en-GB`
- Italian - `it-IT` ⭐ (Default)
- Spanish - `es-ES`
- French - `fr-FR`
- German - `de-DE`

#### Model Selection
- **Whisper Tiny**: Fastest, lowest accuracy
- **Whisper Base**: Good balance (Default)
- **Whisper Small**: Better accuracy, slower
- **Whisper Medium**: Best accuracy, slowest

#### VAD (Voice Activity Detection) Threshold
- **Range**: 0-100%
- **Default**: 30%
- **Purpose**: Filters out background noise
- **Lower value**: More sensitive (picks up quiet speech)
- **Higher value**: Less sensitive (only loud speech)

### 4. Real-time Monitoring

#### Waveform Visualization
- Live audio waveform display
- Color coding:
  - Blue: Normal audio
  - Green: Voice detected (VAD active)

#### Audio Level Meter
- Real-time audio level display
- Color indicators:
  - Green: 0-50% (Good)
  - Orange: 50-75% (Warning - may clip)
  - Red: 75-100% (Danger - clipping likely)
- Shows current, average, min, and max levels

#### Voice Activity Detection
- Visual "Voice Detected" chip when speech is recognized
- Helps verify VAD threshold settings

#### Live Transcription Display
- Shows last 3 transcriptions in real-time
- Displays confidence percentage
- Shows processing latency in milliseconds

### 5. Comprehensive Logging System

Each test session automatically logs:

#### Test Metadata
```json
{
  "timestamp": "2025-11-23T21:45:11.467Z",
  "testDuration": 30.5
}
```

#### Device Information
```json
{
  "device": {
    "id": "device-id-12345",
    "label": "Microphone (2- USB PnP Sound Device)"
  }
}
```

#### Audio Settings
```json
{
  "audioSettings": {
    "sampleRate": 16000,
    "channels": 1,
    "volume": 80,
    "preampGain": 0
  }
}
```

#### Model Settings
```json
{
  "modelSettings": {
    "language": "it-IT",
    "model": "whisper-base",
    "vadThreshold": 0.3
  }
}
```

#### Test Results
```json
{
  "results": {
    "chunksProcessed": 305,
    "transcriptions": [
      {
        "text": "ciao",
        "confidence": 0.87,
        "timestamp": "2025-11-23T21:45:32.423Z",
        "latency": 275
      }
    ],
    "averageLatency": 235.5,
    "averageConfidence": 0.85,
    "audioLevel": {
      "min": 12.3,
      "max": 89.7,
      "average": 45.2
    }
  }
}
```

### 6. Log Export

#### Download Test Logs
- Click the **Save** icon in the header
- Downloads a JSON file with all test logs
- Filename format: `audio-test-log-2025-11-23T21-45-11.json`
- Contains complete test history from current session

#### Log Analysis
Use the exported logs to:
- Compare different microphones
- Optimize audio settings
- Identify best VAD threshold
- Track confidence scores across tests
- Analyze latency patterns
- Debug transcription issues

## Usage Guide

### Running a Basic Test

1. **Select Microphone**
   - Choose your microphone from the dropdown
   - Default microphone is pre-selected

2. **Adjust Volume**
   - Set volume to 70-80% for most microphones
   - Check that volume slider is not muted

3. **Start Test**
   - Click **"Start Test"** button
   - Speak clearly into the microphone
   - Watch the waveform and audio level meter

4. **Monitor Results**
   - Check "Voice Detected" indicator appears when you speak
   - Watch transcriptions appear in real-time
   - Note confidence percentages and latency

5. **Stop Test**
   - Click **"Stop"** button
   - Test log is automatically saved

6. **Review Results**
   - Check test summary at bottom
   - Compare with previous tests
   - Download logs for detailed analysis

### Advanced Testing

#### Testing Different Microphones

```
Test 1: Default USB Microphone
- Device: USB PnP Sound Device
- Volume: 80%
- Preamp: 0 dB
- Language: it-IT
→ Result: Good transcription, 85% avg confidence

Test 2: Headset Microphone
- Device: JBL TOUR PRO2
- Volume: 70%
- Preamp: +5 dB (boost weak signal)
- Language: it-IT
→ Result: Better clarity, 92% avg confidence
```

#### Optimizing Settings

1. **Low Audio Levels**
   - Increase volume to 85-90%
   - Add preamp gain (+5 to +10 dB)
   - Move microphone closer

2. **Too Much Noise**
   - Reduce volume to 60-70%
   - Increase VAD threshold to 40-50%
   - Reduce preamp gain

3. **Poor Transcriptions**
   - Verify correct language is selected
   - Try different model (e.g., whisper-small)
   - Check audio level is in green/yellow range
   - Adjust VAD threshold

4. **High Latency**
   - Use smaller model (whisper-tiny/base)
   - Reduce sample rate to 16000 Hz
   - Check backend performance

## Log File Structure

The exported JSON log file contains an array of test sessions:

```json
[
  {
    "timestamp": "ISO 8601 timestamp",
    "testDuration": "seconds (float)",
    "device": {
      "id": "device identifier",
      "label": "human-readable device name"
    },
    "audioSettings": {
      "sampleRate": "Hz (int)",
      "channels": "1 or 2 (int)",
      "volume": "0-100 (int)",
      "preampGain": "-20 to +20 dB (int)"
    },
    "modelSettings": {
      "language": "BCP 47 language tag",
      "model": "model name string",
      "vadThreshold": "0-1 (float)"
    },
    "results": {
      "chunksProcessed": "total audio chunks (int)",
      "transcriptions": [
        {
          "text": "transcribed text",
          "confidence": "0-1 (float)",
          "timestamp": "ISO 8601 timestamp",
          "latency": "milliseconds (int)"
        }
      ],
      "averageLatency": "milliseconds (float)",
      "averageConfidence": "0-1 (float)",
      "audioLevel": {
        "min": "0-100 (float)",
        "max": "0-100 (float)",
        "average": "0-100 (float)"
      }
    }
  }
]
```

## Tips and Best Practices

### For Best Results

1. **Use a quiet environment** - Background noise affects VAD and transcription
2. **Position microphone 15-30cm from mouth** - Too close causes distortion, too far loses signal
3. **Speak at normal pace** - Not too fast or too slow
4. **Test multiple settings** - Different microphones need different configurations
5. **Monitor audio levels** - Keep in green range (30-60%)
6. **Save logs regularly** - Download logs after important tests
7. **Compare configurations** - Use logs to identify optimal settings

### Troubleshooting

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| No devices shown | Permissions not granted | Refresh devices, check browser/OS permissions |
| No audio level | Microphone not working | Test microphone in system settings |
| Empty transcriptions | VAD threshold too high | Lower VAD to 20-30% |
| Poor accuracy | Wrong language selected | Select correct language (it-IT for Italian) |
| High latency | Model too large | Use whisper-base or whisper-tiny |
| Clipping (red meter) | Volume too high | Reduce volume or add negative preamp gain |
| Weak signal | Volume too low | Increase volume or add positive preamp gain |

## Integration with Backend

The Audio Tester integrates with the RTSTT backend via:

1. **WebSocket connection** - Real-time audio streaming
2. **Audio Bridge** - Handles device access and audio capture
3. **Transcription service** - Processes audio and returns text
4. **Model configuration** - Respects language and model settings

## Future Enhancements

Planned features:
- [ ] Real audio capture integration (currently simulated)
- [ ] Spectrum analyzer visualization
- [ ] Automatic optimal settings detection
- [ ] A/B testing mode (compare two configurations)
- [ ] Cloud log storage
- [ ] Historical trend analysis
- [ ] Export to CSV/Excel
- [ ] Audio recording playback
- [ ] Noise profile analysis

## Support

For issues or questions:
- Check the logs for detailed error messages
- Verify backend is running (`docker-compose up -d`)
- Ensure WebSocket connection is active
- Review this guide for troubleshooting steps

## API Reference

### AudioTester Component Props

```typescript
interface AudioTesterProps {
  // Currently no props, but future versions may include:
  // onTestComplete?: (log: TestLog) => void;
  // defaultLanguage?: string;
  // defaultModel?: string;
}
```

### TestLog Interface

```typescript
interface TestLog {
  timestamp: string;
  testDuration: number;
  device: {
    id: string;
    label: string;
  };
  audioSettings: {
    sampleRate: number;
    channels: number;
    volume: number;
    preampGain: number;
  };
  modelSettings: {
    language: string;
    model: string;
    vadThreshold: number;
  };
  results: {
    chunksProcessed: number;
    transcriptions: Array<{
      text: string;
      confidence: number;
      timestamp: string;
      latency: number;
    }>;
    averageLatency: number;
    averageConfidence: number;
    audioLevel: {
      min: number;
      max: number;
      average: number;
    };
  };
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-11-23
**Component**: `src/ui/desktop/renderer/components/AudioTester/AudioTester.tsx`
