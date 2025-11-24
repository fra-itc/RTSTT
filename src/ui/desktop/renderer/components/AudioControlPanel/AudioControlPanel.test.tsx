/**
 * AudioControlPanel Component Tests (TDD - Track E)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ThemeProvider } from '../../theme';
import { AudioControlPanel } from './AudioControlPanel';

describe('AudioControlPanel', () => {
  const mockDevices = [
    { deviceId: 'device1', label: 'Built-in Microphone' },
    { deviceId: 'device2', label: 'External Mic' },
  ];

  const mockProps = {
    devices: mockDevices,
    selectedDevice: 'device1',
    volume: 80,
    preampGain: 0,
    isRecording: false,
    audioLevel: 0,
    waveformData: new Float32Array([]),
    onDeviceChange: vi.fn(),
    onVolumeChange: vi.fn(),
    onPreampChange: vi.fn(),
    onRecordToggle: vi.fn(),
  };

  it('renders device selector with loaded devices', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    expect(screen.getByLabelText(/microphone device/i)).toBeInTheDocument();
    expect(screen.getByText('Built-in Microphone')).toBeInTheDocument();
  });

  it('shows volume slider with current value', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const volumeSlider = screen.getByLabelText(/volume/i);
    expect(volumeSlider).toBeInTheDocument();
    expect(volumeSlider).toHaveValue('80');
  });

  it('shows preamp gain slider', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const preampSlider = screen.getByLabelText(/preamp gain/i);
    expect(preampSlider).toBeInTheDocument();
  });

  it('displays waveform visualization', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const waveform = screen.getByRole('img', { hidden: true, name: /waveform/i });
    expect(waveform).toBeInTheDocument();
  });

  it('includes record button', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const recordButton = screen.getByRole('button', { name: /start recording/i });
    expect(recordButton).toBeInTheDocument();
  });

  it('shows language selector', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} language="en" />
      </ThemeProvider>
    );

    expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
  });

  it('shows model selector', () => {
    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} model="base" />
      </ThemeProvider>
    );

    expect(screen.getByLabelText(/model/i)).toBeInTheDocument();
  });

  it('has collapsible advanced settings section', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const advancedButton = screen.getByText(/advanced settings/i);
    await user.click(advancedButton);

    expect(screen.getByLabelText(/sample rate/i)).toBeInTheDocument();
  });

  it('calls onDeviceChange when device selected', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const deviceSelector = screen.getByLabelText(/microphone device/i);
    await user.click(deviceSelector);

    const device2 = screen.getByText('External Mic');
    await user.click(device2);

    expect(mockProps.onDeviceChange).toHaveBeenCalledWith('device2');
  });

  it('calls onVolumeChange when volume adjusted', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const volumeSlider = screen.getByLabelText(/volume/i);
    await user.clear(volumeSlider);
    await user.type(volumeSlider, '50');

    expect(mockProps.onVolumeChange).toHaveBeenCalled();
  });

  it('calls onRecordToggle when record button clicked', async () => {
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <AudioControlPanel {...mockProps} />
      </ThemeProvider>
    );

    const recordButton = screen.getByRole('button', { name: /start recording/i });
    await user.click(recordButton);

    expect(mockProps.onRecordToggle).toHaveBeenCalled();
  });
});
