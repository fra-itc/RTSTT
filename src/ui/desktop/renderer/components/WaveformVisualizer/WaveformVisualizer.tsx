/**
 * WaveformVisualizer Component
 * Real-time canvas-based audio waveform visualization
 */

import React, { useRef, useEffect } from 'react';
import { Box, useTheme } from '@mui/material';

export interface WaveformVisualizerProps {
  /** Audio data array (Float32Array from AnalyserNode) */
  data: Float32Array | number[];
  /** Canvas width */
  width: number;
  /** Canvas height */
  height: number;
  /** Color variant */
  color?: 'primary' | 'success' | 'warning' | 'error';
  /** Show VAD threshold line */
  showVadThreshold?: boolean;
  /** VAD threshold value (0-1) */
  vadThreshold?: number;
  /** Show timeline */
  showTimeline?: boolean;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  data,
  width,
  height,
  color = 'primary',
  showVadThreshold = false,
  vadThreshold = 0.3,
  showTimeline = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const theme = useTheme();
  const animationFrameRef = useRef<number>();

  // Get color from theme
  const getColor = () => {
    switch (color) {
      case 'success':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'error':
        return theme.palette.error.main;
      default:
        return theme.palette.primary.main;
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      // Clear canvas
      ctx.fillStyle = theme.palette.mode === 'dark' ? '#1e1e1e' : '#fafafa';
      ctx.fillRect(0, 0, width, height);

      if (!data || data.length === 0) {
        // Draw empty state
        ctx.fillStyle = theme.palette.text.disabled;
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No audio data', width / 2, height / 2);
        return;
      }

      // Draw waveform
      const sliceWidth = width / data.length;
      const centerY = height / 2;

      ctx.beginPath();
      ctx.strokeStyle = getColor();
      ctx.lineWidth = 2;

      for (let i = 0; i < data.length; i++) {
        const value = data[i] || 0;
        const y = centerY + (value * centerY);
        const x = i * sliceWidth;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();

      // Draw VAD threshold line
      if (showVadThreshold) {
        const thresholdY = centerY - (vadThreshold * centerY);

        ctx.beginPath();
        ctx.strokeStyle = theme.palette.warning.main;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.moveTo(0, thresholdY);
        ctx.lineTo(width, thresholdY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label
        ctx.fillStyle = theme.palette.warning.main;
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('VAD', width - 5, thresholdY - 5);
      }
    };

    draw();

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [data, width, height, color, showVadThreshold, vadThreshold, theme]);

  return (
    <Box
      sx={{
        width: '100%',
        height: height,
        backgroundColor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#fafafa',
        borderRadius: 1,
        overflow: 'hidden',
      }}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        role="img"
        aria-label="Audio waveform visualization"
        style={{ display: 'block', width: '100%', height: '100%' }}
      />
    </Box>
  );
};
