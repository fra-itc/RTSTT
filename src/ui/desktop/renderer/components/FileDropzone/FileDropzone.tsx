/**
 * FileDropzone Component
 * Drag-and-drop file upload area for audio files
 */

import React, { useCallback, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  AudioFile as AudioFileIcon,
} from '@mui/icons-material';

interface AudioFile {
  id: string;
  file: File;
  size: number;
  name: string;
}

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  maxFileSize?: number; // in MB
  accept?: string[];
}

const SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.mp4'];
const DEFAULT_MAX_SIZE = 500; // 500MB

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFilesSelected,
  maxFileSize = DEFAULT_MAX_SIZE,
  accept = SUPPORTED_FORMATS,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<AudioFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const validateFile = (file: File): string | null => {
    // Check file extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!accept.includes(ext)) {
      return `Unsupported file format: ${ext}. Supported: ${accept.join(', ')}`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      return `File too large: ${formatFileSize(file.size)}. Maximum: ${maxFileSize}MB`;
    }

    return null;
  };

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;

      setError(null);
      const newFiles: AudioFile[] = [];
      const errors: string[] = [];

      Array.from(files).forEach((file) => {
        const error = validateFile(file);
        if (error) {
          errors.push(`${file.name}: ${error}`);
        } else {
          const audioFile: AudioFile = {
            id: `${Date.now()}-${file.name}`,
            file,
            size: file.size,
            name: file.name,
          };
          newFiles.push(audioFile);
        }
      });

      if (errors.length > 0) {
        setError(errors.join('\n'));
      }

      if (newFiles.length > 0) {
        setSelectedFiles((prev) => [...prev, ...newFiles]);
        onFilesSelected(newFiles.map((af) => af.file));
      }
    },
    [onFilesSelected, accept, maxFileSize]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
      }
    },
    [handleFiles]
  );

  const removeFile = (id: string) => {
    setSelectedFiles((prev) => prev.filter((file) => file.id !== id));
  };

  const clearAll = () => {
    setSelectedFiles([]);
    setError(null);
  };

  return (
    <Box>
      {/* Dropzone Area */}
      <Paper
        elevation={dragActive ? 8 : 2}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        sx={{
          p: 4,
          border: dragActive ? '2px dashed #1976d2' : '2px dashed #ccc',
          backgroundColor: dragActive ? 'action.hover' : 'background.paper',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          '&:hover': {
            backgroundColor: 'action.hover',
            borderColor: 'primary.main',
          },
        }}
      >
        <input
          type="file"
          id="file-upload"
          multiple
          accept={accept.join(',')}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload" style={{ cursor: 'pointer', width: '100%' }}>
          <UploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Drag & Drop Audio Files
          </Typography>
          <Typography variant="body2" color="text.secondary">
            or click to browse
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Chip
              label={`Max ${maxFileSize}MB`}
              size="small"
              sx={{ mr: 1 }}
            />
            <Chip
              label={accept.join(', ')}
              size="small"
            />
          </Box>
        </label>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Selected Files ({selectedFiles.length})
            </Typography>
            <IconButton onClick={clearAll} size="small" color="error">
              <DeleteIcon />
            </IconButton>
          </Box>
          <Paper variant="outlined">
            <List>
              {selectedFiles.map((audioFile, index) => (
                <ListItem
                  key={audioFile.id}
                  divider={index < selectedFiles.length - 1}
                >
                  <AudioFileIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <ListItemText
                    primary={audioFile.name}
                    secondary={formatFileSize(audioFile.size)}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => removeFile(audioFile.id)}
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default FileDropzone;
