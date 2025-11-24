/**
 * AudioControlPanel Component
 * Comprehensive audio control sidebar with device selection, volume, waveform, and recording
 */

import React, { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { RecordButton } from '../RecordButton';
import { WaveformVisualizer } from '../WaveformVisualizer';

export interface AudioDevice {
  deviceId: string;
  label: string;
}

export interface AudioControlPanelProps {
  /** Available audio devices */
  devices: AudioDevice[];
  /** Selected device ID */
  selectedDevice: string;
  /** Volume (0-100) */
  volume: number;
  /** Preamp gain (-12 to +12 dB) */
  preampGain: number;
  /** Is currently recording */
  isRecording: boolean;
  /** Current audio level (0-1) */
  audioLevel: number;
  /** Waveform data */
  waveformData: Float32Array | number[];
  /** Language selection (optional) */
  language?: string;
  /** Model selection (optional) */
  model?: string;
  /** Sample rate (optional) */
  sampleRate?: number;
  /** Channels (optional) */
  channels?: number;
  /** Handlers */
  onDeviceChange: (deviceId: string) => void;
  onVolumeChange: (volume: number) => void;
  onPreampChange: (gain: number) => void;
  onRecordToggle: () => void;
  onLanguageChange?: (language: string) => void;
  onModelChange?: (model: string) => void;
  onRefreshDevices?: () => void;
}

export const AudioControlPanel: React.FC<AudioControlPanelProps> = ({
  devices,
  selectedDevice,
  volume,
  preampGain,
  isRecording,
  audioLevel,
  waveformData,
  language = 'en',
  model = 'base',
  sampleRate = 16000,
  channels = 1,
  onDeviceChange,
  onVolumeChange,
  onPreampChange,
  onRecordToggle,
  onLanguageChange,
  onModelChange,
  onRefreshDevices,
}) => {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  return (
    <Box
      sx={{
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        gap: 3,
        height: '100%',
        overflow: 'auto',
      }}
    >
      {/* Device Selection */}
      <FormControl fullWidth size="small">
        <InputLabel id="device-select-label">Microphone Device</InputLabel>
        <Select
          labelId="device-select-label"
          value={selectedDevice}
          label="Microphone Device"
          onChange={(e) => onDeviceChange(e.target.value)}
          disabled={isRecording}
          endAdornment={
            onRefreshDevices && (
              <Tooltip title="Refresh devices">
                <IconButton
                  size="small"
                  onClick={onRefreshDevices}
                  sx={{ mr: 1 }}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )
          }
        >
          {devices.map((device) => (
            <MenuItem key={device.deviceId} value={device.deviceId}>
              {device.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Volume Control */}
      <Box>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          Volume: {volume}%
        </Typography>
        <Slider
          value={volume}
          onChange={(_, value) => onVolumeChange(value as number)}
          min={0}
          max={100}
          disabled={isRecording}
          aria-label="Volume"
          valueLabelDisplay="auto"
        />
      </Box>

      {/* Preamp Gain */}
      <Box>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          Preamp Gain: {preampGain > 0 ? '+' : ''}{preampGain} dB
        </Typography>
        <Slider
          value={preampGain}
          onChange={(_, value) => onPreampChange(value as number)}
          min={-12}
          max={12}
          disabled={isRecording}
          aria-label="Preamp Gain"
          valueLabelDisplay="auto"
          marks={[
            { value: -12, label: '-12' },
            { value: 0, label: '0' },
            { value: 12, label: '+12' },
          ]}
        />
      </Box>

      <Divider />

      {/* Waveform Visualizer */}
      <Box>
        <Typography variant="caption" color="text.secondary" gutterBottom>
          Audio Waveform
        </Typography>
        <WaveformVisualizer
          width={300}
          height={80}
          data={waveformData}
          color={isRecording ? 'error' : 'primary'}
          showVadThreshold
        />
      </Box>

      {/* Record Button */}
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
        <RecordButton
          recording={isRecording}
          onClick={onRecordToggle}
          size="large"
        />
      </Box>

      <Divider />

      {/* Language Selection */}
      {onLanguageChange && (
        <FormControl fullWidth size="small">
          <InputLabel>Language</InputLabel>
          <Select
            value={language}
            label="Language"
            onChange={(e) => onLanguageChange(e.target.value)}
            disabled={isRecording}
          >
            <MenuItem value="en">English</MenuItem>
            <MenuItem value="it">Italian</MenuItem>
            <MenuItem value="fr">French</MenuItem>
            <MenuItem value="es">Spanish</MenuItem>
            <MenuItem value="de">German</MenuItem>
          </Select>
        </FormControl>
      )}

      {/* Model Selection */}
      {onModelChange && (
        <FormControl fullWidth size="small">
          <InputLabel>Model</InputLabel>
          <Select
            value={model}
            label="Model"
            onChange={(e) => onModelChange(e.target.value)}
            disabled={isRecording}
          >
            <MenuItem value="tiny">Tiny (Fast)</MenuItem>
            <MenuItem value="base">Base</MenuItem>
            <MenuItem value="small">Small</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="large">Large (Accurate)</MenuItem>
          </Select>
        </FormControl>
      )}

      {/* Advanced Settings */}
      <Accordion
        expanded={advancedOpen}
        onChange={() => setAdvancedOpen(!advancedOpen)}
        disableGutters
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="body2">Advanced Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Sample Rate</InputLabel>
              <Select
                value={sampleRate}
                label="Sample Rate"
                disabled={isRecording}
                aria-label="Sample Rate"
              >
                <MenuItem value={8000}>8000 Hz</MenuItem>
                <MenuItem value={16000}>16000 Hz</MenuItem>
                <MenuItem value={24000}>24000 Hz</MenuItem>
                <MenuItem value={48000}>48000 Hz</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth size="small">
              <InputLabel>Channels</InputLabel>
              <Select
                value={channels}
                label="Channels"
                disabled={isRecording}
              >
                <MenuItem value={1}>Mono</MenuItem>
                <MenuItem value={2}>Stereo</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};
