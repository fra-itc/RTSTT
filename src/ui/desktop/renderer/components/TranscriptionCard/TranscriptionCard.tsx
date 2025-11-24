/**
 * TranscriptionCard Component
 * Display individual transcription with confidence, timestamp, and actions
 */

import React from 'react';
import { Card, CardContent, Box, Typography, Chip, IconButton, Tooltip } from '@mui/material';
import { ContentCopy as CopyIcon } from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

export interface TranscriptionCardProps {
  /** Transcription text */
  text: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** ISO timestamp */
  timestamp: string;
  /** Latency in milliseconds */
  latency: number;
  /** Copy handler */
  onCopy?: (text: string) => void;
  /** Edit handler (optional) */
  onEdit?: (text: string) => void;
}

/**
 * Get confidence color based on score
 */
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.5) return 'warning';
  return 'error';
};

/**
 * Format timestamp to relative time
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
  } catch {
    return new Date(timestamp).toLocaleTimeString();
  }
};

export const TranscriptionCard: React.FC<TranscriptionCardProps> = ({
  text,
  confidence,
  timestamp,
  latency,
  onCopy,
  onEdit,
}) => {
  const confidencePercent = Math.round(confidence * 100);
  const confidenceColor = getConfidenceColor(confidence);

  const handleCopy = () => {
    if (onCopy) {
      onCopy(text);
    } else {
      // Fallback to clipboard API
      navigator.clipboard.writeText(text);
    }
  };

  return (
    <Card
      sx={{
        mb: 1.5,
        transition: 'all 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: (theme) => theme.shadows[4],
        },
      }}
    >
      <CardContent>
        {/* Header with confidence and timestamp */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 1,
          }}
        >
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={`${confidencePercent}%`}
              color={confidenceColor}
              size="small"
              sx={{ fontWeight: 600 }}
            />
            <Typography variant="caption" color="text.secondary">
              {latency}ms
            </Typography>
          </Box>

          <Typography variant="caption" color="text.secondary">
            {formatTimestamp(timestamp)}
          </Typography>
        </Box>

        {/* Transcription text */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 1,
          }}
        >
          <Typography variant="body1" sx={{ flex: 1, wordBreak: 'break-word' }}>
            {text}
          </Typography>

          {/* Copy button */}
          <Tooltip title="Copy transcription">
            <IconButton
              size="small"
              onClick={handleCopy}
              aria-label="Copy transcription"
              sx={{
                opacity: 0.7,
                '&:hover': {
                  opacity: 1,
                },
              }}
            >
              <CopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
};
