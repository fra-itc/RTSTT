# Audio Tester - Quick Start Guide

## Prerequisites

1. **Backend Running**: Make sure the RTSTT backend is running
   ```bash
   docker-compose up -d
   ```
   Verify at: http://localhost:8000/health

2. **Node.js**: Ensure Node.js 18+ is installed
   ```bash
   node --version
   ```

## Installation

From the project root:

```bash
# Install dependencies (if not already done)
npm install
```

## Running the Frontend

### Option 1: Development Mode (Recommended for Testing)

```bash
# Start Vite dev server + Electron
npm run dev
```

This will:
- Start Vite dev server on port 5173
- Launch Electron desktop app
- Enable hot module reloading

### Option 2: Production Mode

```bash
# Build and run
npm run build:all
npm start
```

## Using the Audio Tester

### 1. Launch Application

After running `npm run dev`, the Electron window should open automatically showing the RTSTT interface.

### 2. Find Audio Tester

The **Audio Testing Suite** is located in the **top-left panel** of the interface.

### 3. Quick Test (30 seconds)

#### Step 1: Select Your Microphone
- Click the **Microphone Device** dropdown
- You should see all your connected microphones (e.g., "Microphone (2- USB PnP Sound Device)")
- Select the microphone you tested earlier

#### Step 2: Verify Settings
Default settings are optimized for Italian speech:
- ✅ Volume: 80%
- ✅ Language: Italian (it-IT)
- ✅ Model: Whisper Base
- ✅ Sample Rate: 16000 Hz
- ✅ VAD Threshold: 30%

#### Step 3: Start Recording
- Click the blue **"Start Test"** button
- You'll see:
  - Timer starts counting
  - "Recording" chip appears in green
  - Waveform visualization activates

#### Step 4: Speak Into Microphone
- Speak clearly in Italian
- Watch for:
  - Waveform responding to your voice (blue/green waves)
  - "Voice Detected" chip appearing (shows VAD is working)
  - Audio level meter showing 30-60% (green = good)
  - Transcriptions appearing in real-time below the waveform

#### Step 5: Stop Recording
- Click the red **"Stop"** button
- Test log is automatically saved

### 4. Review Results

After stopping, check:
- **Transcriptions panel**: Shows what was recognized
- **Test summary**: Shows number of tests completed
- **Statistics**: Average confidence, latency, audio levels

### 5. Download Logs

- Click the **Save icon** (💾) in the header
- Saves JSON file: `audio-test-log-2025-11-23T21-45-11.json`
- Open with any text editor or JSON viewer

## Adjusting Settings for Better Results

### If Audio Level is Too Low (< 20%)

1. Click **"Advanced Settings"** accordion
2. Under "AUDIO SETTINGS":
   - Increase **Volume** to 90%
   - Set **Preamp Gain** to +5 or +10 dB
3. Try test again

### If Transcriptions are Empty

1. Check **"Voice Detected"** chip appears when you speak
   - If not appearing: Lower VAD threshold to 20%
2. Verify **Language** is correct (it-IT for Italian)
3. Speak louder or move microphone closer

### If Transcriptions are Wrong Language

1. Open **"Advanced Settings"**
2. Under "MODEL SETTINGS":
   - Change **Language** to correct one (e.g., it-IT)
3. Try test again

### If You See Japanese/Chinese Characters (ならなーなーなー)

This happens when:
- Wrong language model is selected
- Try switching to **it-IT** (Italian) or **en-US** (English)

## Comparing Microphones

To compare the 13 microphones you have:

### Test Protocol

For each microphone:

```
1. Select microphone from dropdown
2. Set volume to 80%
3. Start test
4. Speak same phrase: "Questo è un test del microfono numero uno"
5. Record for 10-15 seconds
6. Stop test
7. Note confidence % and transcription quality
8. Repeat for next microphone
```

### Quick Comparison

After testing all microphones:
1. Click **Save icon** to download logs
2. Open JSON file
3. Compare `results.averageConfidence` for each test
4. Best microphone = highest average confidence

Example log comparison:
```json
// Test 1: USB PnP Sound Device
"averageConfidence": 0.85  // 85% - Good

// Test 2: BCC950 ConferenceCam
"averageConfidence": 0.72  // 72% - OK

// Test 3: JBL TOUR PRO2
"averageConfidence": 0.92  // 92% - Excellent! ⭐
```

## Understanding the Log File

Each test creates one entry with:

```json
{
  "device": {
    "label": "Microphone (2- USB PnP Sound Device)"  // Which mic
  },
  "audioSettings": {
    "volume": 80,        // What volume
    "preampGain": 0,     // Any gain applied
    "sampleRate": 16000  // Audio quality
  },
  "modelSettings": {
    "language": "it-IT",     // Language used
    "model": "whisper-base",  // AI model
    "vadThreshold": 0.3       // Voice detection sensitivity
  },
  "results": {
    "transcriptions": [
      {
        "text": "cazzo",      // What was recognized
        "confidence": 0.87,   // How confident (0-1)
        "latency": 275        // How fast (ms)
      }
    ],
    "averageConfidence": 0.85,  // Overall accuracy
    "averageLatency": 235.5,    // Overall speed
    "audioLevel": {
      "average": 45.2           // Audio strength
    }
  }
}
```

## Troubleshooting

### "No devices shown"

**Solution:**
1. Click the **Refresh icon** (🔄) next to Save
2. Check microphone is plugged in
3. Check Windows privacy settings allow microphone access

### "Backend not ready" or connection errors

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# If not running, start it
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Electron window doesn't open

**Solution:**
```bash
# Kill any existing Electron processes
pkill -f electron

# Try again
npm run dev
```

### TypeScript errors

**Solution:**
```bash
# Check types
npm run type-check

# If errors, rebuild
npm run build
```

### "Module not found" errors

**Solution:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

## Advanced Features

### Testing Different Models

1. Open **"Advanced Settings"**
2. Change **Model** dropdown:
   - **Whisper Tiny**: Fastest (lowest quality)
   - **Whisper Base**: Balanced (recommended) ⭐
   - **Whisper Small**: Better quality (slower)
   - **Whisper Medium**: Best quality (slowest)
3. Run same test with each model
4. Compare latency vs confidence

### Testing Different Sample Rates

1. Open **"Advanced Settings"**
2. Change **Sample Rate**:
   - **8000 Hz**: Phone quality (not recommended)
   - **16000 Hz**: Speech optimized (recommended) ⭐
   - **44100 Hz**: CD quality (overkill for speech)
   - **48000 Hz**: Studio quality (overkill for speech)
3. Higher rate = more bandwidth, not necessarily better

### Finding Optimal VAD Threshold

1. Open **"Advanced Settings"**
2. Start with **VAD Threshold: 30%**
3. Run test, check if "Voice Detected" appears when speaking
4. If not appearing: Lower to 20%
5. If appearing when silent: Raise to 40-50%
6. Optimal = detects speech, ignores silence

## Tips for Production Use

### Best Practices

1. **Test in actual environment**
   - Same room noise level
   - Same distance from microphone
   - Same speaking style

2. **Run multiple tests**
   - At least 3 tests per configuration
   - Use average of results

3. **Document your findings**
   - Save logs with descriptive names
   - Note environmental factors
   - Record any issues

4. **Monitor over time**
   - Test periodically
   - Check if performance degrades
   - Update settings as needed

### Recommended Settings for Italian

Based on your test results:

```
Microphone: [Your best mic from comparison]
Volume: 70-80%
Preamp Gain: 0 dB (adjust if needed)
Sample Rate: 16000 Hz
Channels: Mono
Language: it-IT
Model: whisper-base
VAD Threshold: 30%
```

## Next Steps

After finding optimal settings:

1. **Update backend configuration** with best settings
2. **Document in team wiki** for other developers
3. **Set up monitoring** to track performance over time
4. **Create baseline** for future comparisons

## Support

Issues? Check:
- [Full Audio Tester Guide](./AUDIO_TESTER_GUIDE.md)
- Backend logs: `docker-compose logs -f`
- Frontend console: Open DevTools (Ctrl+Shift+I)

---

**Quick Reference:**

- 🎤 Select microphone → Click dropdown
- ▶️ Start test → Blue "Start Test" button
- ⏹️ Stop test → Red "Stop" button
- ⚙️ Adjust settings → "Advanced Settings" accordion
- 💾 Save logs → Save icon in header
- 🔄 Refresh devices → Refresh icon in header

**Default Port:** Frontend runs on port 5173 (dev mode)
**Backend:** http://localhost:8000
