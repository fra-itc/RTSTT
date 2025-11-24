/**
 * SuggestionsPanel Component
 * Displays AI-generated suggestions and summaries based on transcription content
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Skeleton,
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  Divider,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  ContentCopy as ContentCopyIcon,
  Summarize as SummarizeIcon,
} from '@mui/icons-material';

export interface SuggestionsPanelProps {
  summary?: string;
  suggestions?: string[];
  isLoading?: boolean;
  isEmpty?: boolean;
}

export const SuggestionsPanel: React.FC<SuggestionsPanelProps> = ({
  summary,
  suggestions = [],
  isLoading = false,
  isEmpty = false,
}) => {
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [copiedItem, setCopiedItem] = useState<string>('');

  const handleCopy = (text: string, itemName: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedItem(itemName);
      setSnackbarOpen(true);
    });
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  // Show empty state
  if (isEmpty && !isLoading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Stack spacing={2} alignItems="center" justifyContent="center" sx={{ minHeight: 300 }}>
            <AutoAwesomeIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
            <Typography variant="h6" color="text.secondary" align="center">
              No Suggestions Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Continue recording to receive AI-powered insights
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1, overflow: 'auto' }}>
          <Stack spacing={3}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesomeIcon color="secondary" />
              <Typography variant="h6">AI Suggestions</Typography>
            </Box>

            {/* Summary Section */}
            {(summary || isLoading) && (
              <>
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SummarizeIcon fontSize="small" color="action" />
                      <Typography variant="subtitle2" color="text.secondary">
                        Summary
                      </Typography>
                    </Box>
                    {summary && !isLoading && (
                      <Tooltip title="Copy summary">
                        <IconButton
                          size="small"
                          onClick={() => handleCopy(summary, 'summary')}
                          sx={{ ml: 1 }}
                        >
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>

                  {isLoading ? (
                    <Stack spacing={1}>
                      <Skeleton variant="text" width="100%" />
                      <Skeleton variant="text" width="90%" />
                      <Skeleton variant="text" width="95%" />
                    </Stack>
                  ) : summary ? (
                    <Card
                      variant="outlined"
                      sx={{
                        bgcolor: 'background.default',
                        p: 2,
                        transition: 'all 0.2s ease',
                        '&:hover': {
                          boxShadow: 1,
                        },
                      }}
                    >
                      <Typography
                        variant="body2"
                        color="text.primary"
                        sx={{
                          lineHeight: 1.7,
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {summary}
                      </Typography>
                    </Card>
                  ) : null}
                </Box>

                {suggestions.length > 0 && <Divider />}
              </>
            )}

            {/* Suggestions Section */}
            {(suggestions.length > 0 || isLoading) && (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <AutoAwesomeIcon fontSize="small" color="action" />
                  <Typography variant="subtitle2" color="text.secondary">
                    Recommendations
                  </Typography>
                </Box>

                {isLoading ? (
                  <Stack spacing={2}>
                    {[1, 2, 3].map((i) => (
                      <Card key={i} variant="outlined" sx={{ bgcolor: 'background.default', p: 2 }}>
                        <Skeleton variant="text" width="100%" />
                        <Skeleton variant="text" width="80%" />
                      </Card>
                    ))}
                  </Stack>
                ) : (
                  <Stack spacing={1.5}>
                    {suggestions.map((suggestion, index) => (
                      <Card
                        key={index}
                        variant="outlined"
                        sx={{
                          bgcolor: 'background.default',
                          p: 2,
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 2,
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            boxShadow: 1,
                            bgcolor: 'action.hover',
                          },
                        }}
                      >
                        <Box
                          sx={{
                            minWidth: 24,
                            height: 24,
                            borderRadius: '50%',
                            bgcolor: 'secondary.main',
                            color: 'secondary.contrastText',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            flexShrink: 0,
                          }}
                        >
                          {index + 1}
                        </Box>
                        <Typography
                          variant="body2"
                          color="text.primary"
                          sx={{
                            flexGrow: 1,
                            lineHeight: 1.6,
                          }}
                        >
                          {suggestion}
                        </Typography>
                        <Tooltip title="Copy suggestion">
                          <IconButton
                            size="small"
                            onClick={() => handleCopy(suggestion, `suggestion ${index + 1}`)}
                            sx={{ flexShrink: 0, mt: -0.5 }}
                          >
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Card>
                    ))}
                  </Stack>
                )}
              </Box>
            )}

            {/* No data available message */}
            {!summary && suggestions.length === 0 && !isLoading && (
              <Typography variant="body2" color="text.secondary" fontStyle="italic" align="center">
                AI suggestions will appear as you record
              </Typography>
            )}
          </Stack>
        </CardContent>
      </Card>

      {/* Copy confirmation snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity="success" sx={{ width: '100%' }}>
          {copiedItem} copied to clipboard!
        </Alert>
      </Snackbar>
    </>
  );
};
