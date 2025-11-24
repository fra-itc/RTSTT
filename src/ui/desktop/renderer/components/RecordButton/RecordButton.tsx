/**
 * RecordButton Component
 * Large, animated button for starting/stopping recording
 */

import React from 'react';
import { Box, IconButton, Typography, styled, keyframes } from '@mui/material';
import { Mic as MicIcon, Stop as StopIcon } from '@mui/icons-material';

export interface RecordButtonProps {
  /** Whether currently recording */
  recording?: boolean;
  /** Recording duration in seconds (for timer display) */
  duration?: number;
  /** Whether button is disabled */
  disabled?: boolean;
  /** Button size variant */
  size?: 'small' | 'medium' | 'large';
  /** Enable pulse animation when recording */
  pulse?: boolean;
  /** Click handler */
  onClick: () => void;
}

// Pulse animation for recording state
const pulseAnimation = keyframes`
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0);
  }
`;

// Styled button with size variants
const StyledButton = styled(IconButton, {
  shouldForwardProp: (prop) =>
    prop !== 'recording' && prop !== 'pulse' && prop !== 'buttonSize',
})<{ recording?: boolean; pulse?: boolean; buttonSize: number }>(
  ({ theme, recording, pulse, buttonSize }) => ({
    width: buttonSize,
    height: buttonSize,
    borderRadius: '50%',
    backgroundColor: recording
      ? theme.palette.error.main
      : theme.palette.primary.main,
    color: theme.palette.common.white,
    transition: theme.transitions.create(['transform', 'box-shadow', 'background-color'], {
      duration: theme.transitions.duration.short,
    }),
    boxShadow: theme.shadows[3],

    '&:hover': {
      backgroundColor: recording
        ? theme.palette.error.dark
        : theme.palette.primary.dark,
      transform: 'scale(1.05)',
      boxShadow: theme.shadows[6],
    },

    '&:active': {
      transform: 'scale(0.98)',
    },

    '&:disabled': {
      backgroundColor: theme.palette.action.disabledBackground,
      color: theme.palette.action.disabled,
      opacity: 0.5,
    },

    ...(recording && pulse && {
      animation: `${pulseAnimation} 2s infinite`,
    }),
  })
);

// Timer display
const TimerText = styled(Typography)(({ theme }) => ({
  position: 'absolute',
  bottom: -28,
  left: '50%',
  transform: 'translateX(-50%)',
  fontSize: theme.typography.caption.fontSize,
  fontWeight: theme.typography.fontWeightMedium,
  color: theme.palette.text.secondary,
  fontFamily: theme.typography.fontFamily,
  whiteSpace: 'nowrap',
}));

// Size mapping
const sizeMap = {
  small: 48,
  medium: 64,
  large: 80,
};

// Icon size mapping
const iconSizeMap = {
  small: 24,
  medium: 32,
  large: 40,
};

/**
 * Format seconds to MM:SS
 */
const formatDuration = (seconds: number = 0): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const RecordButton: React.FC<RecordButtonProps> = ({
  recording = false,
  duration,
  disabled = false,
  size = 'large',
  pulse = true,
  onClick,
}) => {
  const buttonSize = sizeMap[size];
  const iconSize = iconSizeMap[size];

  const ariaLabel = recording ? 'Stop recording' : 'Start recording';

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <StyledButton
        recording={recording}
        pulse={pulse}
        buttonSize={buttonSize}
        disabled={disabled}
        onClick={onClick}
        aria-label={ariaLabel}
        aria-pressed={recording}
        sx={{ width: `${buttonSize}px`, height: `${buttonSize}px` }}
      >
        {recording ? (
          <StopIcon sx={{ fontSize: iconSize }} />
        ) : (
          <MicIcon sx={{ fontSize: iconSize }} />
        )}
      </StyledButton>

      {/* Timer display when recording */}
      {recording && duration !== undefined && (
        <TimerText variant="caption">
          {formatDuration(duration)}
        </TimerText>
      )}
    </Box>
  );
};
