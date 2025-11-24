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
            sx={{
              p: 4,
              textAlign: 'center',
              backgroundColor: (theme) =>
                theme.palette.mode === 'dark' ? '#1e1e1e' : '#fafafa',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No transcriptions yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {searchQuery
                ? 'No results found for your search.'
                : 'Start recording to see transcriptions appear here.'}
            </Typography>
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
