/**
 * useAudioPipeline Hook
 * Integration layer connecting UI components to audio backend
 * Extracted from working AudioTester component (track3 branch)
 */

import { useState, useRef, useEffect, useCallback } from 'react';

export interface AudioDevice {
  deviceId: string;
  label: string;
}

export interface Transcription {
  text: string;
  confidence: number;
  timestamp: string;
  latency: number;
}

export interface Keyword {
  keyword: string;
  score: number;
}

export interface NamedEntity {
  text: string;
  type: string;
  confidence?: number;
}

export interface Sentiment {
  label: string;
  score: number;
  positive?: number;
  neutral?: number;
  negative?: number;
}

export interface Insights {
  keywords: Keyword[];
  entities: NamedEntity[];
  sentiment?: Sentiment;
}

export interface AudioPipelineState {
  // Device management
  devices: AudioDevice[];
  selectedDevice: string;
  isLoadingDevices: boolean;

  // Recording state
  isRecording: boolean;
  recordingDuration: number;

  // WebSocket connection
  isConnected: boolean;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  websocketUrl: string;
  wsError: string | null;

  // Audio settings
  volume: number;
  isMuted: boolean;
  preampGain: number;
  sampleRate: number;
  channels: number;

  // Model settings
  language: string;
  model: string;
  vadThreshold: number;

  // Real-time data
  audioLevel: number;
  waveformData: Float32Array;
  transcriptions: Transcription[];
  chunksProcessed: number;

  // NLP Insights
  insights: Insights;
  summary: string;
  suggestions: string[];

  // Handlers
  loadDevices: () => Promise<void>;
  setSelectedDevice: (deviceId: string) => void;
  setWebsocketUrl: (url: string) => void;
  handleRecordToggle: () => Promise<void>;
  handleVolumeChange: (volume: number) => void;
  handlePreampChange: (gain: number) => void;
  handleLanguageChange: (language: string) => void;
  handleModelChange: (model: string) => void;
  wsConnect: () => void;
  wsDisconnect: () => void;
  clearTranscriptions: () => void;
}

/**
 * Get default WebSocket URL based on current location
 */
const getDefaultWebSocketUrl = (): string => {
  if (typeof window === 'undefined') return 'ws://localhost:8000/ws';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname;
  return `${protocol}//${hostname}:8000/ws`;
};

export const useAudioPipeline = (): AudioPipelineState => {
  // Device state
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [isLoadingDevices, setIsLoadingDevices] = useState(true);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const isRecordingRef = useRef(false);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // WebSocket state
  const [websocketUrl, setWebsocketUrl] = useState<string>(getDefaultWebSocketUrl());
  const [isConnected, setIsConnected] = useState(false);
  const isConnectedRef = useRef(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [wsError, setWsError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Audio settings
  const [volume, setVolume] = useState(80);
  const [isMuted] = useState(false);
  const [preampGain, setPreampGain] = useState(0);
  const [sampleRate] = useState(16000);
  const [channels] = useState(1);

  // Model settings
  const [language, setLanguage] = useState('en');
  const [model, setModel] = useState('base');
  const [vadThreshold] = useState(0.3);

  // Real-time monitoring
  const [audioLevel, setAudioLevel] = useState(0);
  const [waveformData, setWaveformData] = useState<Float32Array>(new Float32Array(128));
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [chunksProcessed, setChunksProcessed] = useState(0);

  // NLP Insights state
  const [insights, setInsights] = useState<Insights>({
    keywords: [],
    entities: [],
    sentiment: undefined,
  });
  const [summary, setSummary] = useState<string>('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Web Audio API refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const audioProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const animationFrameRef = useRef<number>();

  /**
   * Load audio devices
   */
  const loadDevices = useCallback(async () => {
    setIsLoadingDevices(true);
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices
        .filter((device) => device.kind === 'audioinput')
        .map((device) => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 5)}`,
        }));

      setDevices(audioInputs);

      if (audioInputs.length > 0 && !selectedDevice) {
        setSelectedDevice(audioInputs[0].deviceId);
      }
    } catch (error) {
      console.error('Failed to load audio devices:', error);
    } finally {
      setIsLoadingDevices(false);
    }
  }, [selectedDevice]);

  /**
   * WebSocket connect
   */
  const wsConnect = useCallback(() => {
    console.log('[useAudioPipeline] Starting WebSocket connection...');

    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionStatus('connecting');
    setWsError(null);

    try {
      const ws = new WebSocket(websocketUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✓ WebSocket connected!');
        setIsConnected(true);
        isConnectedRef.current = true;
        setConnectionStatus('connected');
        setWsError(null);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        isConnectedRef.current = false;
        setConnectionStatus('disconnected');
        wsRef.current = null;
      };

      ws.onerror = (event) => {
        console.error('[useAudioPipeline] WebSocket error:', event);
        setIsConnected(false);
        isConnectedRef.current = false;
        setConnectionStatus('error');
        setWsError('Connection error occurred');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('[useAudioPipeline] Received message type:', message.type);

          // Handle transcription results
          if (message.type === 'transcription_segment' || message.type === 'transcription') {
            let text = '';
            let confidence = 0.85;
            let latency = 0;

            // Format 1: {transcription: {text, confidence}, latency: {total_ms}}
            if (message.transcription && message.transcription.text) {
              text = message.transcription.text;
              confidence = message.transcription.confidence || 0.85;
              latency = message.latency?.total_ms || 0;
            }
            // Format 2: {text, language, latency_ms}
            else if (message.text !== undefined) {
              text = message.text;
              confidence = message.confidence || 0.85;
              latency = message.latency_ms || 0;
            }
            // Format 3: Legacy {data: {text}}
            else if (message.data && message.data.text) {
              text = message.data.text;
              confidence = message.data.confidence || 0.85;
              latency = message.data.latency || 0;
            }

            // Only add non-empty transcriptions
            if (text && text.trim().length > 0) {
              console.log('[useAudioPipeline] Adding transcription:', text);
              setTranscriptions((prev) => [
                ...prev,
                {
                  text,
                  confidence,
                  timestamp: new Date().toISOString(),
                  latency,
                },
              ]);
            }
          }
          // Handle NLP insights
          else if (message.type === 'nlp_insights' || message.type === 'insights') {
            console.log('[useAudioPipeline] Received NLP insights:', message);
            const data = message.data || message;

            // Update keywords
            if (data.keywords && Array.isArray(data.keywords)) {
              setInsights((prev) => ({
                ...prev,
                keywords: data.keywords.map((kw: any) => ({
                  keyword: kw.keyword || kw.text || kw,
                  score: kw.score || kw.confidence || 1.0,
                })),
              }));
            }

            // Update entities
            if (data.entities && Array.isArray(data.entities)) {
              setInsights((prev) => ({
                ...prev,
                entities: data.entities.map((ent: any) => ({
                  text: ent.text || ent.entity || ent,
                  type: ent.type || ent.label || 'MISC',
                  confidence: ent.confidence || ent.score,
                })),
              }));
            }

            // Update sentiment
            if (data.sentiment) {
              setInsights((prev) => ({
                ...prev,
                sentiment: {
                  label: data.sentiment.label || data.sentiment.sentiment || 'Neutral',
                  score: data.sentiment.score || data.sentiment.confidence || 0.5,
                  positive: data.sentiment.positive,
                  neutral: data.sentiment.neutral,
                  negative: data.sentiment.negative,
                },
              }));
            }
          }
          // Handle summary
          else if (message.type === 'summary') {
            console.log('[useAudioPipeline] Received summary:', message);
            const summaryText = message.summary || message.data?.summary || message.text;
            if (summaryText && summaryText.trim().length > 0) {
              setSummary(summaryText);
            }
          }
          // Handle suggestions
          else if (message.type === 'suggestions') {
            console.log('[useAudioPipeline] Received suggestions:', message);
            const suggestionsList = message.suggestions || message.data?.suggestions || [];
            if (Array.isArray(suggestionsList) && suggestionsList.length > 0) {
              setSuggestions(suggestionsList);
            }
          }
          // Handle combined results (all in one message)
          else if (message.type === 'results' || message.type === 'analysis_complete') {
            console.log('[useAudioPipeline] Received combined results:', message);
            const data = message.data || message;

            // Process all insights at once
            if (data.insights) {
              if (data.insights.keywords) {
                setInsights((prev) => ({
                  ...prev,
                  keywords: data.insights.keywords.map((kw: any) => ({
                    keyword: kw.keyword || kw.text || kw,
                    score: kw.score || kw.confidence || 1.0,
                  })),
                }));
              }
              if (data.insights.entities) {
                setInsights((prev) => ({
                  ...prev,
                  entities: data.insights.entities.map((ent: any) => ({
                    text: ent.text || ent.entity || ent,
                    type: ent.type || ent.label || 'MISC',
                    confidence: ent.confidence || ent.score,
                  })),
                }));
              }
              if (data.insights.sentiment) {
                setInsights((prev) => ({
                  ...prev,
                  sentiment: {
                    label: data.insights.sentiment.label || 'Neutral',
                    score: data.insights.sentiment.score || 0.5,
                    positive: data.insights.sentiment.positive,
                    neutral: data.insights.sentiment.neutral,
                    negative: data.insights.sentiment.negative,
                  },
                }));
              }
            }

            if (data.summary) {
              setSummary(data.summary);
            }

            if (data.suggestions && Array.isArray(data.suggestions)) {
              setSuggestions(data.suggestions);
            }
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };
    } catch (error) {
      console.error('[useAudioPipeline] Failed to create WebSocket:', error);
      setConnectionStatus('error');
      setWsError(`Failed to create connection: ${(error as Error)?.message}`);
    }
  }, [websocketUrl]);

  /**
   * WebSocket disconnect
   */
  const wsDisconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
    isConnectedRef.current = false;
    setConnectionStatus('disconnected');
  }, []);

  /**
   * WebSocket send
   */
  const wsSend = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
    }
  }, []);

  /**
   * Initialize audio capture
   */
  const initializeAudioCapture = useCallback(async () => {
    try {
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

      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: sampleRate,
      });
      audioContextRef.current = audioContext;

      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;

      const gainNode = audioContext.createGain();
      gainNodeRef.current = gainNode;

      const volumeGain = isMuted ? 0 : volume / 100;
      const preampGainLinear = Math.pow(10, preampGain / 20);
      gainNode.gain.value = volumeGain * preampGainLinear;

      const source = audioContext.createMediaStreamSource(stream);
      source.connect(gainNode);
      gainNode.connect(analyser);

      // Create script processor for audio data
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, channels, channels);
      audioProcessorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current || !isConnectedRef.current) {
          return;
        }

        const inputData = event.inputBuffer.getChannelData(0);

        // Convert to PCM16
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send to backend
        try {
          const bytes = new Uint8Array(pcmData.buffer);
          const base64 = btoa(String.fromCharCode(...bytes));

          wsSend({
            type: 'audio_chunk',
            data: {
              audio: base64,
              sampleRate: sampleRate,
              channels: channels,
              language: language,
              model: model,
            },
          });

          setChunksProcessed((prev) => prev + 1);
        } catch (error) {
          console.error('Failed to send audio chunk:', error);
        }
      };

      analyser.connect(processor);
      processor.connect(audioContext.destination);

      // Start visualization
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateVisualization = () => {
        if (!isRecordingRef.current) return;

        analyser.getByteTimeDomainData(dataArray);

        // Calculate RMS audio level
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          const normalized = (dataArray[i] - 128) / 128;
          sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / bufferLength);
        setAudioLevel(Math.min(100, rms * 100 * 3));

        // Update waveform data (downsample for display)
        const downsampleFactor = Math.floor(bufferLength / 128);
        const waveform = new Float32Array(128);
        for (let i = 0; i < 128; i++) {
          waveform[i] = (dataArray[i * downsampleFactor] - 128) / 128;
        }
        setWaveformData(waveform);

        animationFrameRef.current = requestAnimationFrame(updateVisualization);
      };

      updateVisualization();

      console.log('Audio capture initialized successfully');
    } catch (error) {
      console.error('Failed to initialize audio capture:', error);
      throw error;
    }
  }, [selectedDevice, sampleRate, channels, volume, isMuted, preampGain, language, model, wsSend]);

  /**
   * Stop audio capture
   */
  const stopAudioCapture = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    if (audioProcessorRef.current) {
      audioProcessorRef.current.disconnect();
      audioProcessorRef.current = null;
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    if (gainNodeRef.current) {
      gainNodeRef.current.disconnect();
      gainNodeRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    setAudioLevel(0);
    setWaveformData(new Float32Array(128));
  }, []);

  /**
   * Handle record toggle
   */
  const handleRecordToggle = useCallback(async () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      isRecordingRef.current = false;
      setRecordingStartTime(null);
      setRecordingDuration(0);
      setChunksProcessed(0);
      stopAudioCapture();
    } else {
      // Start recording
      setIsRecording(true);
      isRecordingRef.current = true;
      setRecordingStartTime(Date.now());
      setChunksProcessed(0);

      // Connect to WebSocket if not already connected
      if (!isConnected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        wsConnect();
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      // Initialize audio capture
      await initializeAudioCapture();
    }
  }, [isRecording, isConnected, wsConnect, initializeAudioCapture, stopAudioCapture]);

  /**
   * Update recording duration
   */
  useEffect(() => {
    if (!isRecording || !recordingStartTime) return;

    const interval = setInterval(() => {
      const elapsed = (Date.now() - recordingStartTime) / 1000;
      setRecordingDuration(elapsed);
    }, 100);

    return () => clearInterval(interval);
  }, [isRecording, recordingStartTime]);

  /**
   * Load devices on mount
   */
  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopAudioCapture();
      wsDisconnect();
    };
  }, [stopAudioCapture, wsDisconnect]);

  return {
    // Device management
    devices,
    selectedDevice,
    isLoadingDevices,

    // Recording state
    isRecording,
    recordingDuration,

    // WebSocket connection
    isConnected,
    connectionStatus,
    websocketUrl,
    wsError,

    // Audio settings
    volume,
    isMuted,
    preampGain,
    sampleRate,
    channels,

    // Model settings
    language,
    model,
    vadThreshold,

    // Real-time data
    audioLevel,
    waveformData,
    transcriptions,
    chunksProcessed,

    // NLP Insights
    insights,
    summary,
    suggestions,

    // Handlers
    loadDevices,
    setSelectedDevice,
    setWebsocketUrl,
    handleRecordToggle,
    handleVolumeChange: setVolume,
    handlePreampChange: setPreampGain,
    handleLanguageChange: setLanguage,
    handleModelChange: setModel,
    wsConnect,
    wsDisconnect,
    clearTranscriptions: () => {
      setTranscriptions([]);
      setInsights({ keywords: [], entities: [], sentiment: undefined });
      setSummary('');
      setSuggestions([]);
    },
  };
};
