/**
 * TranscriptionList Component
 * List container for transcription cards with search and export
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Menu,
  MenuItem,
  InputAdornment,
  Paper,
} from '@mui/material';
import {
  Search as SearchIcon,
  FileDownload as ExportIcon,
  Mic as MicIcon,
  ArrowBack as ArrowIcon,
} from '@mui/icons-material';
import { TranscriptionCard } from '../TranscriptionCard';

export interface Transcription {
  text: string;
  confidence: number;
  timestamp: string;
  latency: number;
}

export interface TranscriptionListProps {
  /** Array of transcriptions */
  transcriptions: Transcription[];
  /** Export handler */
  onExport?: (format: 'txt' | 'json' | 'srt', data: Transcription[]) => void;
}

export const TranscriptionList: React.FC<TranscriptionListProps> = ({
  transcriptions,
  onExport,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null);

  // Filter transcriptions based on search
  const filteredTranscriptions = useMemo(() => {
    if (!searchQuery) return transcriptions;

    const query = searchQuery.toLowerCase();
    return transcriptions.filter((t) =>
      t.text.toLowerCase().includes(query)
    );
  }, [transcriptions, searchQuery]);

  const handleExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setExportAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportAnchor(null);
  };

  const handleExportFormat = (format: 'txt' | 'json' | 'srt') => {
    if (onExport) {
      onExport(format, transcriptions);
    }
    handleExportClose();
  };

  // Handle copy
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header with search and export */}
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          mb: 2,
          alignItems: 'center',
        }}
      >
        <TextField
          fullWidth
          size="small"
          placeholder="Search transcriptions..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />

        <Button
          variant="outlined"
          startIcon={<ExportIcon />}
          onClick={handleExportClick}
          disabled={transcriptions.length === 0}
          aria-label="Export transcriptions"
        >
          Export
        </Button>

        <Menu
          anchorEl={exportAnchor}
          open={Boolean(exportAnchor)}
          onClose={handleExportClose}
        >
          <MenuItem onClick={() => handleExportFormat('txt')}>
            Export as TXT
          </MenuItem>
          <MenuItem onClick={() => handleExportFormat('json')}>
            Export as JSON
          </MenuItem>
          <MenuItem onClick={() => handleExportFormat('srt')}>
            Export as SRT
          </MenuItem>
        </Menu>
      </Box>

      {/* Transcription list */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          pr: 1,
        }}
      >
        {filteredTranscriptions.length === 0 ? (
          <Paper
            elevation={0}
            sx={{
              p: 6,
              textAlign: 'center',
              backgroundColor: (theme) =>
                theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
              border: (theme) =>
                `2px dashed ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
              borderRadius: 3,
            }}
          >
            {searchQuery ? (
              // Search results empty state
              <>
                <SearchIcon
                  sx={{
                    fontSize: 64,
                    color: 'text.disabled',
                    mb: 2,
                  }}
                />
                <Typography variant="h5" color="text.secondary" gutterBottom>
                  No results found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Try adjusting your search query
                </Typography>
              </>
            ) : (
              // Initial empty state
              <>
                <Box
                  sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    bgcolor: (theme) =>
                      theme.palette.mode === 'dark' ? 'rgba(33, 150, 243, 0.1)' : 'rgba(33, 150, 243, 0.08)',
                    mb: 3,
                  }}
                >
                  <MicIcon
                    sx={{
                      fontSize: 64,
                      color: 'primary.main',
                    }}
                  />
                </Box>

                <Typography variant="h4" color="text.primary" gutterBottom fontWeight={600}>
                  Ready to transcribe
                </Typography>

                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
                  Your transcriptions will appear here in real-time as you speak
                </Typography>

                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                    maxWidth: 400,
                    mx: 'auto',
                    textAlign: 'left',
                    mb: 3,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        minWidth: 32,
                        height: 32,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: 14,
                      }}
                    >
                      1
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Select your microphone device from the sidebar
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        minWidth: 32,
                        height: 32,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: 14,
                      }}
                    >
                      2
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Adjust volume and preamp gain if needed
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        minWidth: 32,
                        height: 32,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: 14,
                      }}
                    >
                      3
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Click the blue record button to start
                    </Typography>
                  </Box>
                </Box>

                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 1,
                    color: 'primary.main',
                    fontSize: 14,
                  }}
                >
                  <ArrowIcon sx={{ transform: 'rotate(180deg)', fontSize: 20 }} />
                  <Typography variant="caption" color="primary.main" fontWeight={600}>
                    Start recording from the sidebar
                  </Typography>
                </Box>
              </>
            )}
          </Paper>
        ) : (
          filteredTranscriptions.map((transcription, index) => (
            <TranscriptionCard
              key={`${transcription.timestamp}-${index}`}
              {...transcription}
              onCopy={handleCopy}
            />
          ))
        )}
      </Box>
    </Box>
  );
};
