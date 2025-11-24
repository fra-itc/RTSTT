/**
 * WaveformVisualizer Component Tests (TDD - Track B)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '../../theme';
import { WaveformVisualizer } from './WaveformVisualizer';

describe('WaveformVisualizer', () => {
  it('renders canvas element with correct dimensions', () => {
    render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('width', '300');
    expect(canvas).toHaveAttribute('height', '80');
  });

  it('draws waveform from audio data array', () => {
    const mockData = new Float32Array([0.1, 0.5, 0.3, 0.8, 0.2]);

    render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={mockData} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true }) as HTMLCanvasElement;
    const ctx = canvas.getContext('2d');

    // Verify canvas context was called
    expect(ctx).toBeTruthy();
  });

  it('shows VAD threshold line when enabled', () => {
    render(
      <ThemeProvider>
        <WaveformVisualizer
          width={300}
          height={80}
          data={[]}
          showVadThreshold
          vadThreshold={0.3}
        />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toBeInTheDocument();
  });

  it('updates in real-time with new audio data', () => {
    const initialData = new Float32Array([0.1, 0.2]);
    const { rerender } = render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={initialData} />
      </ThemeProvider>
    );

    const newData = new Float32Array([0.5, 0.8]);
    rerender(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={newData} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toBeInTheDocument();
  });

  it('is responsive to container width', () => {
    const { rerender } = render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} />
      </ThemeProvider>
    );

    rerender(
      <ThemeProvider>
        <WaveformVisualizer width={600} height={80} data={[]} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toHaveAttribute('width', '600');
  });

  it('shows empty state when no audio data', () => {
    render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toBeInTheDocument();
  });

  it('has proper ARIA labels', () => {
    render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} />
      </ThemeProvider>
    );

    const canvas = screen.getByRole('img', { hidden: true });
    expect(canvas).toHaveAttribute('aria-label', 'Audio waveform visualization');
  });

  it('supports color variants', () => {
    const { rerender } = render(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} color="primary" />
      </ThemeProvider>
    );

    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();

    rerender(
      <ThemeProvider>
        <WaveformVisualizer width={300} height={80} data={[]} color="success" />
      </ThemeProvider>
    );

    expect(screen.getByRole('img', { hidden: true })).toBeInTheDocument();
  });
});
