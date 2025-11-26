/**
 * BatchJobList Component
 * Displays and manages batch transcription jobs with real-time status updates
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Collapse,
  Alert,
  Button,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Autorenew as ProcessingIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  files_processed: number;
  total_files: number;
  current_file?: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

interface BatchJobListProps {
  jobs: JobStatus[];
  onDownload?: (jobId: string, format: string) => void;
  onRefresh?: (jobId: string) => void;
}

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon sx={{ color: 'success.main' }} />;
    case 'failed':
      return <ErrorIcon sx={{ color: 'error.main' }} />;
    case 'processing':
      return <ProcessingIcon sx={{ color: 'info.main' }} />;
    case 'pending':
    default:
      return <PendingIcon sx={{ color: 'warning.main' }} />;
  }
};

const StatusChip: React.FC<{ status: string }> = ({ status }) => {
  const colorMap: Record<string, any> = {
    pending: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'error',
  };

  return (
    <Chip
      label={status.toUpperCase()}
      color={colorMap[status] || 'default'}
      size="small"
      sx={{ fontWeight: 'bold' }}
    />
  );
};

const JobItem: React.FC<{
  job: JobStatus;
  onDownload?: (jobId: string, format: string) => void;
  onRefresh?: (jobId: string) => void;
}> = ({ job, onDownload, onRefresh }) => {
  const [expanded, setExpanded] = useState(false);

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString();
  };

  const handleDownload = (format: string) => {
    if (onDownload) {
      onDownload(job.job_id, format);
    }
  };

  return (
    <Paper elevation={2} sx={{ mb: 2 }}>
      <ListItem
        sx={{
          flexDirection: 'column',
          alignItems: 'stretch',
          p: 2,
        }}
      >
        {/* Job Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StatusIcon status={job.status} />
            <Typography variant="subtitle1" sx={{ fontFamily: 'monospace' }}>
              {job.job_id.substring(0, 8)}...
            </Typography>
            <StatusChip status={job.status} />
          </Box>
          <Box>
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Progress Bar */}
        {(job.status === 'processing' || job.status === 'pending') && (
          <Box sx={{ width: '100%', mb: 1 }}>
            <LinearProgress
              variant="determinate"
              value={job.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              {job.files_processed} / {job.total_files} files ({Math.round(job.progress)}%)
            </Typography>
          </Box>
        )}

        {/* Summary Info */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            Files: {job.total_files}
          </Typography>
          {job.current_file && (
            <Typography variant="body2" color="text.secondary">
              Current: {job.current_file}
            </Typography>
          )}
        </Box>

        {/* Expanded Details */}
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            {/* Timestamps */}
            <Typography variant="body2" color="text.secondary">
              Started: {formatDate(job.started_at)}
            </Typography>
            {job.completed_at && (
              <Typography variant="body2" color="text.secondary">
                Completed: {formatDate(job.completed_at)}
              </Typography>
            )}

            {/* Error Display */}
            {job.error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {job.error}
              </Alert>
            )}

            {/* Download Options */}
            {job.status === 'completed' && onDownload && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Download Transcription:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {['txt', 'srt', 'vtt', 'json'].map((format) => (
                    <Button
                      key={format}
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(format)}
                    >
                      {format.toUpperCase()}
                    </Button>
                  ))}
                </Box>
              </Box>
            )}

            {/* Refresh Button for Failed Jobs */}
            {job.status === 'failed' && onRefresh && (
              <Box sx={{ mt: 2 }}>
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => onRefresh(job.job_id)}
                >
                  Retry
                </Button>
              </Box>
            )}
          </Box>
        </Collapse>
      </ListItem>
    </Paper>
  );
};

export const BatchJobList: React.FC<BatchJobListProps> = ({
  jobs,
  onDownload,
  onRefresh,
}) => {
  if (jobs.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No batch jobs yet. Upload audio files to get started.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Batch Jobs ({jobs.length})
      </Typography>
      <List>
        {jobs.map((job) => (
          <JobItem
            key={job.job_id}
            job={job}
            onDownload={onDownload}
            onRefresh={onRefresh}
          />
        ))}
      </List>
    </Box>
  );
};

export default BatchJobList;
