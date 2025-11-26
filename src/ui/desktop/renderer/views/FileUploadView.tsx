/**
 * FileUploadView Component
 * Main view for audio file upload and batch transcription
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  PlayArrow as StartIcon,
} from '@mui/icons-material';
import axios from 'axios';

import FileDropzone from '../components/FileDropzone/FileDropzone';
import BatchJobList from '../components/BatchJobList/BatchJobList';

interface UploadedFile {
  file_id: string;
  filename: string;
  file_size: number;
  file: File;
}

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

// Get backend URL from environment
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

export const FileUploadView: React.FC = () => {
  // File upload state
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  // Transcription settings
  const [provider, setProvider] = useState('whisper');
  const [language, setLanguage] = useState('auto');
  const [model, setModel] = useState('base');
  const [exportFormats, setExportFormats] = useState<string[]>(['txt']);

  // Batch jobs
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [processing, setProcessing] = useState(false);

  // UI state
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Handle file selection
  const handleFilesSelected = useCallback((files: File[]) => {
    setSelectedFiles((prev) => [...prev, ...files]);
  }, []);

  // Upload files to backend
  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      showSnackbar('No files selected', 'warning');
      return;
    }

    setUploading(true);
    const uploaded: UploadedFile[] = [];

    try {
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(`${BACKEND_URL}/api/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        if (response.data.success) {
          uploaded.push({
            file_id: response.data.file_id,
            filename: response.data.filename,
            file_size: response.data.file_size,
            file,
          });
        }
      }

      setUploadedFiles((prev) => [...prev, ...uploaded]);
      setSelectedFiles([]);
      showSnackbar(`Successfully uploaded ${uploaded.length} file(s)`, 'success');
    } catch (error: any) {
      console.error('Upload error:', error);
      showSnackbar(
        error.response?.data?.detail || 'Failed to upload files',
        'error'
      );
    } finally {
      setUploading(false);
    }
  };

  // Start batch transcription
  const handleStartTranscription = async () => {
    if (uploadedFiles.length === 0) {
      showSnackbar('No files uploaded', 'warning');
      return;
    }

    setProcessing(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/batch/transcribe`, {
        file_ids: uploadedFiles.map((f) => f.file_id),
        provider,
        language: language === 'auto' ? null : language,
        model,
        export_formats: exportFormats,
      });

      if (response.data.success) {
        const newJob: JobStatus = {
          job_id: response.data.job_id,
          status: 'pending',
          progress: 0,
          files_processed: 0,
          total_files: response.data.file_count,
        };

        setJobs((prev) => [newJob, ...prev]);
        setUploadedFiles([]);
        showSnackbar('Batch transcription started', 'success');

        // Start polling for job status
        pollJobStatus(response.data.job_id);
      }
    } catch (error: any) {
      console.error('Transcription error:', error);
      showSnackbar(
        error.response?.data?.detail || 'Failed to start transcription',
        'error'
      );
    } finally {
      setProcessing(false);
    }
  };

  // Poll job status
  const pollJobStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/batch/status/${jobId}`
        );

        setJobs((prev) =>
          prev.map((job) =>
            job.job_id === jobId ? { ...job, ...response.data } : job
          )
        );

        // Stop polling if job is complete or failed
        if (['completed', 'failed'].includes(response.data.status)) {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Poll error:', error);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    // Clean up on unmount
    return () => clearInterval(pollInterval);
  };

  // Download transcription
  const handleDownload = async (jobId: string, format: string) => {
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/batch/download/${jobId}/${format}`,
        {
          responseType: 'blob',
        }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transcription_${jobId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      showSnackbar(`Downloaded transcription as ${format.toUpperCase()}`, 'success');
    } catch (error: any) {
      console.error('Download error:', error);
      showSnackbar('Failed to download transcription', 'error');
    }
  };

  // Show snackbar notification
  const showSnackbar = (
    message: string,
    severity: 'success' | 'error' | 'info' | 'warning'
  ) => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Audio File Upload & Batch Transcription
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload audio files for batch transcription processing
      </Typography>

      <Grid container spacing={3}>
        {/* Left Column: Upload & Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              1. Upload Audio Files
            </Typography>
            <FileDropzone onFilesSelected={handleFilesSelected} />

            {selectedFiles.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
                  onClick={handleUpload}
                  disabled={uploading}
                  fullWidth
                >
                  {uploading ? 'Uploading...' : `Upload ${selectedFiles.length} File(s)`}
                </Button>
              </Box>
            )}
          </Paper>

          {uploadedFiles.length > 0 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                2. Configure Transcription
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Provider</InputLabel>
                    <Select
                      value={provider}
                      label="Provider"
                      onChange={(e) => setProvider(e.target.value)}
                    >
                      <MenuItem value="whisper">Whisper (Local)</MenuItem>
                      <MenuItem value="openai">OpenAI Whisper API</MenuItem>
                      <MenuItem value="deepgram">Deepgram</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={language}
                      label="Language"
                      onChange={(e) => setLanguage(e.target.value)}
                    >
                      <MenuItem value="auto">Auto Detect</MenuItem>
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="es">Spanish</MenuItem>
                      <MenuItem value="fr">French</MenuItem>
                      <MenuItem value="de">German</MenuItem>
                      <MenuItem value="it">Italian</MenuItem>
                      <MenuItem value="pt">Portuguese</MenuItem>
                      <MenuItem value="zh">Chinese</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Model Size</InputLabel>
                    <Select
                      value={model}
                      label="Model Size"
                      onChange={(e) => setModel(e.target.value)}
                    >
                      <MenuItem value="tiny">Tiny (fastest)</MenuItem>
                      <MenuItem value="base">Base</MenuItem>
                      <MenuItem value="small">Small</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="large">Large (best quality)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Export Formats</InputLabel>
                    <Select
                      multiple
                      value={exportFormats}
                      label="Export Formats"
                      onChange={(e) =>
                        setExportFormats(
                          typeof e.target.value === 'string'
                            ? e.target.value.split(',')
                            : e.target.value
                        )
                      }
                    >
                      <MenuItem value="txt">TXT (Plain Text)</MenuItem>
                      <MenuItem value="srt">SRT (Subtitles)</MenuItem>
                      <MenuItem value="vtt">VTT (WebVTT)</MenuItem>
                      <MenuItem value="json">JSON (Full Data)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={processing ? <CircularProgress size={20} /> : <StartIcon />}
                    onClick={handleStartTranscription}
                    disabled={processing}
                    fullWidth
                    size="large"
                  >
                    {processing ? 'Starting...' : `Start Transcription (${uploadedFiles.length} files)`}
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          )}
        </Grid>

        {/* Right Column: Batch Jobs */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <BatchJobList
              jobs={jobs}
              onDownload={handleDownload}
            />
          </Paper>
        </Grid>
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default FileUploadView;
