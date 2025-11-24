import React, { useRef, useEffect, useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Box,
  Button,
  IconButton,
  Typography,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  LinearProgress,
  Paper,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
} from '@mui/material';
import {
  Mic as MicIcon,
  Stop as StopIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
  GraphicEq as GraphicEqIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { useWebSocket } from '../../hooks/useWebSocket';

interface AudioDevice {
  deviceId: string;
  label: string;
  kind: string;
  groupId?: string;
}

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

export const AudioTester: React.FC = () => {
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // Audio devices
  const [audioDevices, setAudioDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [isLoadingDevices, setIsLoadingDevices] = useState(true);

  // Audio settings
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);
  const [preampGain, setPreampGain] = useState(0); // dB: -20 to +20
  const [sampleRate, setSampleRate] = useState(16000);
  const [channels, setChannels] = useState(1);

  // Model settings
  const [language, setLanguage] = useState('it-IT'); // Italian
  const [modelName, setModelName] = useState('whisper-base');
  const [vadThreshold, setVadThreshold] = useState(0.3);

  // Real-time monitoring
  const [audioLevel, setAudioLevel] = useState(0);
  const [vadActive, setVadActive] = useState(false);
  const [transcriptions, setTranscriptions] = useState<Array<{
    text: string;
    confidence: number;
    timestamp: string;
    latency: number;
  }>>([]);

  // Statistics
  const [chunksProcessed, setChunksProcessed] = useState(0);
  const [audioLevelStats, setAudioLevelStats] = useState({
    min: 0,
    max: 0,
    average: 0,
    samples: [] as number[],
  });

  // Canvas for visualization
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();

  // Log state
  const [testLogs, setTestLogs] = useState<TestLog[]>([]);

  // Web Audio API refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioDataArrayRef = useRef<Uint8Array | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const audioProcessorRef = useRef<ScriptProcessorNode | null>(null);

  // WebSocket connection for backend communication
  const {
    isConnected,
    connect: wsConnect,
    disconnect: wsDisconnect,
    send: wsSend,
    connectionStatus,
    error: wsError,
  } = useWebSocket({
    autoConnect: false,
    onMessage: (message) => {
      // Handle transcription results from backend
      if (message.type === 'transcription_segment' && message.data) {
        const startTime = performance.now();
        const latency = message.data.latency || Math.floor(performance.now() - startTime);

        setTranscriptions(prev => [
          ...prev,
          {
            text: message.data.text,
            confidence: message.data.confidence || 0.85,
            timestamp: new Date().toISOString(),
            latency: latency,
          },
        ]);
      }
    },
  });

  // Load audio devices
  const loadAudioDevices = async () => {
    setIsLoadingDevices(true);
    try {
      // Try Electron API first
      if (window.electronAPI?.audio?.getDevices) {
        const result = await window.electronAPI.audio.getDevices();
        if (result.success && result.devices) {
          setAudioDevices(result.devices);
          if (result.devices.length > 0 && !selectedDevice) {
            setSelectedDevice(result.devices[0].deviceId);
          }
        }
      } else {
        // Fallback to Web API
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(d => d.kind === 'audioinput').map(d => ({
          deviceId: d.deviceId,
          label: d.label || `Microphone ${d.deviceId.slice(0, 8)}`,
          kind: d.kind,
          groupId: d.groupId,
        }));
        setAudioDevices(audioInputs);
        if (audioInputs.length > 0 && !selectedDevice) {
          setSelectedDevice(audioInputs[0].deviceId);
        }
      }
    } catch (error) {
      console.error('Failed to load audio devices:', error);
    } finally {
      setIsLoadingDevices(false);
    }
  };

  useEffect(() => {
    loadAudioDevices();
  }, []);

  // Update recording duration
  useEffect(() => {
    if (!isRecording || !recordingStartTime) return;

    const interval = setInterval(() => {
      setRecordingDuration((Date.now() - recordingStartTime) / 1000);
    }, 100);

    return () => clearInterval(interval);
  }, [isRecording, recordingStartTime]);

  // Initialize Web Audio API and capture real audio
  const initializeAudioCapture = async () => {
    try {
      // Request microphone access
      const constraints: MediaStreamConstraints = {
        audio: {
          deviceId: selectedDevice ? { exact: selectedDevice } : undefined,
          sampleRate: sampleRate,
          channelCount: channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: false,
        },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;

      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: sampleRate,
      });
      audioContextRef.current = audioContext;

      // Create analyser node for visualization and level detection
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;

      // Create data array for waveform
      const bufferLength = analyser.frequencyBinCount;
      audioDataArrayRef.current = new Uint8Array(bufferLength);

      // Create gain node for volume and preamp control
      const gainNode = audioContext.createGain();
      gainNodeRef.current = gainNode;

      // Apply volume and preamp gain
      const volumeGain = isMuted ? 0 : volume / 100;
      const preampGainLinear = Math.pow(10, preampGain / 20); // Convert dB to linear
      gainNode.gain.value = volumeGain * preampGainLinear;

      // Create source from microphone stream
      const source = audioContext.createMediaStreamSource(stream);

      // Connect: source -> gain -> analyser
      source.connect(gainNode);
      gainNode.connect(analyser);

      // Create script processor for audio data capture (for sending to backend)
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, channels, channels);
      audioProcessorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (!isRecording || !isConnected) return;

        // Get audio data
        const inputData = event.inputBuffer.getChannelData(0);

        // Convert to Int16Array (PCM16)
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send audio chunk to backend WebSocket
        try {
          // Convert Int16Array to base64 for transmission
          const bytes = new Uint8Array(pcmData.buffer);
          const base64 = btoa(String.fromCharCode(...bytes));

          wsSend({
            type: 'audio_chunk',
            data: {
              audio: base64,
              sampleRate: sampleRate,
              channels: channels,
              language: language,
              model: modelName,
            },
          });

          setChunksProcessed(prev => prev + 1);
        } catch (error) {
          console.error('Failed to send audio chunk:', error);
        }
      };

      // Connect analyser to processor to destination
      analyser.connect(processor);
      processor.connect(audioContext.destination);

      console.log('Audio capture initialized successfully');
    } catch (error) {
      console.error('Failed to initialize audio capture:', error);
      alert(`Failed to access microphone: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Cleanup audio resources
  const cleanupAudioCapture = () => {
    if (audioProcessorRef.current) {
      audioProcessorRef.current.disconnect();
      audioProcessorRef.current = null;
    }

    if (gainNodeRef.current) {
      gainNodeRef.current.disconnect();
      gainNodeRef.current = null;
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    audioDataArrayRef.current = null;
  };

  // Update audio levels from real audio data
  useEffect(() => {
    if (!isRecording || !analyserRef.current || !audioDataArrayRef.current) return;

    const updateAudioLevel = () => {
      if (!analyserRef.current || !audioDataArrayRef.current) return;

      // Get time domain data (waveform)
      analyserRef.current.getByteTimeDomainData(audioDataArrayRef.current);

      // Calculate RMS (Root Mean Square) for audio level
      let sum = 0;
      for (let i = 0; i < audioDataArrayRef.current.length; i++) {
        const normalized = (audioDataArrayRef.current[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / audioDataArrayRef.current.length);
      const newLevel = Math.min(100, rms * 100 * 3); // Scale to 0-100

      setAudioLevel(newLevel);
      setVadActive(newLevel > vadThreshold * 100);

      // Update statistics
      setAudioLevelStats(prev => {
        const newSamples = [...prev.samples, newLevel];
        const sum = newSamples.reduce((a, b) => a + b, 0);
        return {
          min: Math.min(prev.min === 0 ? newLevel : prev.min, newLevel),
          max: Math.max(prev.max, newLevel),
          average: sum / newSamples.length,
          samples: newSamples.slice(-100), // Keep last 100 samples
        };
      });
    };

    // Update at 60 FPS for smooth visualization
    const intervalId = setInterval(updateAudioLevel, 1000 / 60);

    return () => clearInterval(intervalId);
  }, [isRecording, vadThreshold]);

  // Draw waveform visualization with real audio data
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const animate = () => {
      if (!canvas || !ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      ctx.fillStyle = '#1e1e1e';
      ctx.fillRect(0, 0, width, height);

      if (isRecording && analyserRef.current && audioDataArrayRef.current) {
        // Get real waveform data
        analyserRef.current.getByteTimeDomainData(audioDataArrayRef.current);

        ctx.strokeStyle = vadActive ? '#4caf50' : '#90caf9';
        ctx.lineWidth = 2;
        ctx.beginPath();

        const sliceWidth = width / audioDataArrayRef.current.length;
        let x = 0;

        for (let i = 0; i < audioDataArrayRef.current.length; i++) {
          const v = audioDataArrayRef.current[i] / 128.0;
          const y = (v * height) / 2;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }

          x += sliceWidth;
        }

        ctx.lineTo(width, height / 2);
        ctx.stroke();

        // Draw center line
        ctx.strokeStyle = '#3e3e42';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
      } else {
        // No audio - draw flat line
        ctx.strokeStyle = '#3e3e42';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRecording, vadActive]);

  const handleRecordingToggle = async () => {
    if (isRecording) {
      // Stop recording and save log
      const log: TestLog = {
        timestamp: new Date().toISOString(),
        testDuration: recordingDuration,
        device: {
          id: selectedDevice,
          label: audioDevices.find(d => d.deviceId === selectedDevice)?.label || 'Unknown',
        },
        audioSettings: {
          sampleRate,
          channels,
          volume: isMuted ? 0 : volume,
          preampGain,
        },
        modelSettings: {
          language,
          model: modelName,
          vadThreshold,
        },
        results: {
          chunksProcessed,
          transcriptions,
          averageLatency: transcriptions.length > 0
            ? transcriptions.reduce((sum, t) => sum + t.latency, 0) / transcriptions.length
            : 0,
          averageConfidence: transcriptions.length > 0
            ? transcriptions.reduce((sum, t) => sum + t.confidence, 0) / transcriptions.length
            : 0,
          audioLevel: {
            min: audioLevelStats.min,
            max: audioLevelStats.max,
            average: audioLevelStats.average,
          },
        },
      };

      setTestLogs(prev => [...prev, log]);

      // Cleanup audio resources
      cleanupAudioCapture();

      // Disconnect WebSocket
      wsDisconnect();

      // Reset state
      setIsRecording(false);
      setRecordingStartTime(null);
      setRecordingDuration(0);
      setAudioLevel(0);
      setVadActive(false);
      setTranscriptions([]);
      setChunksProcessed(0);
      setAudioLevelStats({ min: 0, max: 0, average: 0, samples: [] });
    } else {
      // Start recording
      setIsRecording(true);
      setRecordingStartTime(Date.now());
      setTranscriptions([]);
      setChunksProcessed(0);
      setAudioLevelStats({ min: 0, max: 0, average: 0, samples: [] });

      // Connect to WebSocket backend
      wsConnect();

      // Wait a bit for WebSocket to connect
      await new Promise(resolve => setTimeout(resolve, 500));

      // Initialize audio capture
      await initializeAudioCapture();
    }
  };

  const handleSaveLog = () => {
    const logData = JSON.stringify(testLogs, null, 2);
    const blob = new Blob([logData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audio-test-log-${new Date().toISOString().replace(/:/g, '-')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getAudioLevelColor = () => {
    if (audioLevel < 50) return 'success';
    if (audioLevel < 75) return 'warning';
    return 'error';
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <CardHeader
        avatar={<GraphicEqIcon color="primary" />}
        title="Audio Testing Suite"
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh Devices">
              <IconButton size="small" onClick={loadAudioDevices} disabled={isRecording}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Save Test Logs">
              <IconButton size="small" onClick={handleSaveLog} disabled={testLogs.length === 0}>
                <SaveIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
        subheader={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Chip
              size="small"
              label={isRecording ? `Recording ${formatDuration(recordingDuration)}` : 'Ready'}
              color={isRecording ? 'success' : 'default'}
              sx={{
                animation: isRecording ? 'pulse 1.5s ease-in-out infinite' : 'none',
              }}
            />
            {/* Connection Status Indicator */}
            <Tooltip title={`Backend: ${connectionStatus}${wsError ? ` - ${wsError}` : ''}`}>
              <Chip
                size="small"
                icon={
                  connectionStatus === 'connected' ? <CheckCircleIcon /> :
                  connectionStatus === 'error' ? <ErrorIcon /> :
                  <SyncIcon />
                }
                label={
                  connectionStatus === 'connected' ? 'Connected' :
                  connectionStatus === 'connecting' ? 'Connecting...' :
                  connectionStatus === 'reconnecting' ? 'Reconnecting...' :
                  connectionStatus === 'error' ? 'Error' :
                  'Disconnected'
                }
                color={
                  connectionStatus === 'connected' ? 'success' :
                  connectionStatus === 'error' ? 'error' :
                  'default'
                }
                variant={isConnected ? 'filled' : 'outlined'}
                sx={{
                  animation: connectionStatus === 'connecting' || connectionStatus === 'reconnecting' ? 'pulse 1.5s ease-in-out infinite' : 'none',
                }}
              />
            </Tooltip>
            {vadActive && (
              <Chip
                size="small"
                label="Voice Detected"
                color="primary"
                sx={{ animation: 'pulse 1s ease-in-out infinite' }}
              />
            )}
            {isRecording && (
              <Chip
                size="small"
                label={`${chunksProcessed} chunks`}
                variant="outlined"
              />
            )}
          </Box>
        }
        sx={{ pb: 1 }}
      />

      <CardContent
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          overflow: 'auto',
          pt: 0,
        }}
      >
        {/* Waveform Canvas */}
        <Box
          sx={{
            height: 150,
            position: 'relative',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
            overflow: 'hidden',
          }}
        >
          <canvas
            ref={canvasRef}
            style={{
              width: '100%',
              height: '100%',
              display: 'block',
            }}
          />
        </Box>

        {/* Audio Level Meter */}
        {isRecording && (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Audio Level
              </Typography>
              <Typography variant="caption" color={`${getAudioLevelColor()}.main`} fontWeight={600}>
                {Math.round(audioLevel)}% (avg: {Math.round(audioLevelStats.average)}%)
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={audioLevel}
              color={getAudioLevelColor()}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>
        )}

        {/* Connection Error Alert */}
        {wsError && (
          <Alert severity="error" onClose={() => {}}>
            <Typography variant="body2">
              <strong>Backend Connection Error:</strong> {wsError}
            </Typography>
            <Typography variant="caption">
              Make sure the backend is running at ws://localhost:8000/ws
            </Typography>
          </Alert>
        )}

        {/* Recent Transcriptions */}
        {transcriptions.length > 0 && (
          <Paper variant="outlined" sx={{ p: 1.5, maxHeight: 100, overflow: 'auto' }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Recent Transcriptions ({transcriptions.length})
            </Typography>
            {transcriptions.slice(-3).reverse().map((t, i) => (
              <Box key={i} sx={{ mt: 0.5 }}>
                <Typography variant="body2">
                  "{t.text}"
                  <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    {(t.confidence * 100).toFixed(0)}% • {t.latency}ms
                  </Typography>
                </Typography>
              </Box>
            ))}
          </Paper>
        )}

        {/* No Transcriptions Yet - Show Waiting Message */}
        {isRecording && transcriptions.length === 0 && chunksProcessed > 50 && (
          <Alert severity="info">
            <Typography variant="body2">
              Listening for speech... Speak into your microphone to see transcriptions appear here.
            </Typography>
          </Alert>
        )}

        {/* Main Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Tooltip title={isRecording ? 'Stop Recording' : 'Start Recording'}>
            <Button
              variant="contained"
              size="large"
              color={isRecording ? 'error' : 'primary'}
              onClick={handleRecordingToggle}
              startIcon={isRecording ? <StopIcon /> : <MicIcon />}
              sx={{ minWidth: 150 }}
            >
              {isRecording ? 'Stop' : 'Start Test'}
            </Button>
          </Tooltip>

          <FormControl fullWidth size="small">
            <InputLabel>Microphone Device</InputLabel>
            <Select
              value={selectedDevice}
              label="Microphone Device"
              onChange={(e) => setSelectedDevice(e.target.value)}
              disabled={isRecording || isLoadingDevices}
            >
              {audioDevices.map((device) => (
                <MenuItem key={device.deviceId} value={device.deviceId}>
                  {device.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Volume Control */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60 }}>
            Volume
          </Typography>
          <Tooltip title={isMuted ? 'Unmute' : 'Mute'}>
            <IconButton
              size="small"
              onClick={() => setIsMuted(!isMuted)}
              color={isMuted ? 'error' : 'default'}
            >
              {isMuted ? <VolumeOffIcon /> : <VolumeUpIcon />}
            </IconButton>
          </Tooltip>
          <Slider
            value={isMuted ? 0 : volume}
            onChange={(_, value) => setVolume(value as number)}
            disabled={isMuted || isRecording}
            size="small"
            sx={{ flex: 1 }}
            marks={[
              { value: 0, label: '0%' },
              { value: 50, label: '50%' },
              { value: 100, label: '100%' },
            ]}
          />
          <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
            {isMuted ? 0 : volume}%
          </Typography>
        </Box>

        <Divider />

        {/* Advanced Settings */}
        <Accordion elevation={0}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon fontSize="small" />
              <Typography variant="subtitle2">Advanced Settings</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {/* Audio Settings */}
              <Grid item xs={12}>
                <Typography variant="caption" color="primary" fontWeight={600}>
                  AUDIO SETTINGS
                </Typography>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Sample Rate</InputLabel>
                  <Select
                    value={sampleRate}
                    label="Sample Rate"
                    onChange={(e) => setSampleRate(Number(e.target.value))}
                    disabled={isRecording}
                  >
                    <MenuItem value={8000}>8000 Hz</MenuItem>
                    <MenuItem value={16000}>16000 Hz</MenuItem>
                    <MenuItem value={44100}>44100 Hz</MenuItem>
                    <MenuItem value={48000}>48000 Hz</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Channels</InputLabel>
                  <Select
                    value={channels}
                    label="Channels"
                    onChange={(e) => setChannels(Number(e.target.value))}
                    disabled={isRecording}
                  >
                    <MenuItem value={1}>Mono</MenuItem>
                    <MenuItem value={2}>Stereo</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  Preamp Gain: {preampGain > 0 ? '+' : ''}{preampGain} dB
                </Typography>
                <Slider
                  value={preampGain}
                  onChange={(_, value) => setPreampGain(value as number)}
                  disabled={isRecording}
                  min={-20}
                  max={20}
                  step={1}
                  marks={[
                    { value: -20, label: '-20' },
                    { value: 0, label: '0' },
                    { value: 20, label: '+20' },
                  ]}
                  size="small"
                />
              </Grid>

              {/* Model Settings */}
              <Grid item xs={12} sx={{ mt: 2 }}>
                <Typography variant="caption" color="primary" fontWeight={600}>
                  MODEL SETTINGS
                </Typography>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={language}
                    label="Language"
                    onChange={(e) => setLanguage(e.target.value)}
                    disabled={isRecording}
                  >
                    <MenuItem value="en-US">English (US)</MenuItem>
                    <MenuItem value="en-GB">English (UK)</MenuItem>
                    <MenuItem value="it-IT">Italian</MenuItem>
                    <MenuItem value="es-ES">Spanish</MenuItem>
                    <MenuItem value="fr-FR">French</MenuItem>
                    <MenuItem value="de-DE">German</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Model</InputLabel>
                  <Select
                    value={modelName}
                    label="Model"
                    onChange={(e) => setModelName(e.target.value)}
                    disabled={isRecording}
                  >
                    <MenuItem value="whisper-tiny">Whisper Tiny</MenuItem>
                    <MenuItem value="whisper-base">Whisper Base</MenuItem>
                    <MenuItem value="whisper-small">Whisper Small</MenuItem>
                    <MenuItem value="whisper-medium">Whisper Medium</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">
                  VAD Threshold: {(vadThreshold * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={vadThreshold}
                  onChange={(_, value) => setVadThreshold(value as number)}
                  disabled={isRecording}
                  min={0}
                  max={1}
                  step={0.05}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 0.5, label: '50%' },
                    { value: 1, label: '100%' },
                  ]}
                  size="small"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Test History */}
        {testLogs.length > 0 && (
          <Alert severity="info" sx={{ mt: 1 }}>
            <Typography variant="body2">
              {testLogs.length} test{testLogs.length > 1 ? 's' : ''} completed.
              <Button size="small" onClick={handleSaveLog} sx={{ ml: 1 }}>
                Download Logs
              </Button>
            </Typography>
          </Alert>
        )}
      </CardContent>

      <style>
        {`
          @keyframes pulse {
            0%, 100% {
              opacity: 1;
            }
            50% {
              opacity: 0.6;
            }
          }
        `}
      </style>
    </Card>
  );
};
