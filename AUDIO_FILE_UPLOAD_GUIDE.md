# Audio File Upload & Batch Transcription Guide

## Overview

This feature enables users to upload audio files and process them in batch mode for transcription. The system supports multiple audio formats, parallel processing, and various export formats.

## Architecture

### Backend Components

1. **File Upload Handler** (`src/agents/orchestrator/file_upload_handler.py`)
   - REST API endpoints for file upload and job management
   - File validation (format, size)
   - Job status tracking
   - Download endpoints for results

2. **Batch Processor** (`src/core/batch_processor/`)
   - Celery-based task queue for parallel processing
   - Redis for job metadata and results storage
   - Whisper integration for transcription
   - Support for 4 concurrent workers

3. **Export Formatters** (`src/core/batch_processor/exporters.py`)
   - TXT: Plain text with timestamps
   - SRT: Standard subtitle format
   - VTT: WebVTT format
   - JSON: Full metadata with confidence scores

### Frontend Components

1. **FileDropzone** (`src/ui/desktop/renderer/components/FileDropzone/`)
   - Drag-and-drop file upload
   - File validation and preview
   - Multiple file selection

2. **BatchJobList** (`src/ui/desktop/renderer/components/BatchJobList/`)
   - Real-time job status display
   - Progress tracking
   - Download options

3. **FileUploadView** (`src/ui/desktop/renderer/views/FileUploadView.tsx`)
   - Main interface combining upload and job management
   - Provider/model/language selection
   - Export format configuration

## Installation

### Prerequisites

1. Redis server running on port 6380
2. Python dependencies installed

### Install Dependencies

```bash
# Install batch processing dependencies
pip install -r requirements-batch.txt

# Or install specific packages
pip install celery redis aiofiles python-multipart httpx
```

### Start Services

1. **Start Redis** (if not already running):
```bash
redis-server --port 6380
```

2. **Start Celery Worker**:
```bash
./scripts/start_celery_worker.sh
```

3. **Start Backend API**:
```bash
uvicorn src.agents.orchestrator.fastapi_app:app --host 0.0.0.0 --port 8001 --reload
```

4. **Start Frontend**:
```bash
npm run dev
```

## API Endpoints

### Upload Audio File
```http
POST /api/upload
Content-Type: multipart/form-data

file: <audio file>

Response:
{
  "success": true,
  "file_id": "uuid",
  "filename": "example.mp3",
  "file_size": 1024000,
  "file_path": "/tmp/uploads/uuid.mp3",
  "upload_timestamp": "2025-11-26T12:00:00Z"
}
```

### Start Batch Transcription
```http
POST /api/batch/transcribe
Content-Type: application/json

{
  "file_ids": ["uuid1", "uuid2"],
  "provider": "whisper",
  "language": "en",
  "model": "base",
  "export_formats": ["txt", "srt", "vtt", "json"]
}

Response:
{
  "success": true,
  "job_id": "job-uuid",
  "file_count": 2,
  "status": "pending"
}
```

### Check Job Status
```http
GET /api/batch/status/{job_id}

Response:
{
  "job_id": "job-uuid",
  "status": "processing",
  "progress": 50.0,
  "files_processed": 1,
  "total_files": 2,
  "current_file": "example2.mp3",
  "started_at": "2025-11-26T12:01:00Z"
}
```

### Get Job Results
```http
GET /api/batch/result/{job_id}

Response:
{
  "job_id": "job-uuid",
  "status": "completed",
  "results": [
    {
      "file_name": "example.mp3",
      "success": true,
      "text": "Transcribed text...",
      "segments": [...],
      "language": "en",
      "confidence": 0.95
    }
  ],
  "total_duration": 45.2,
  "completed_at": "2025-11-26T12:02:00Z"
}
```

### Download Transcription
```http
GET /api/batch/download/{job_id}/{format}

Formats: txt, srt, vtt, json

Response: File download
```

## Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- OGG (.ogg)
- M4A (.m4a)
- MP4 (.mp4)

**Maximum file size**: 500MB per file

## Configuration

### Celery Settings (`src/core/batch_processor/celery_app.py`)

- **Concurrency**: 4 parallel workers
- **Task timeout**: 1 hour (3600s)
- **Result TTL**: 24 hours
- **Queue**: `audio_processing`

### Redis Configuration

Set in `.env.local`:
```bash
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
```

### STT Service

Set in `.env.local`:
```bash
STT_SERVICE_HOST=localhost
STT_SERVICE_PORT=50054
```

## Usage Example

### 1. Upload Files via Frontend

1. Navigate to File Upload view
2. Drag and drop audio files or click to browse
3. Files are validated (format and size)
4. Click "Upload" to send files to backend

### 2. Configure Transcription

- **Provider**: Choose STT provider (Whisper, OpenAI, Deepgram)
- **Language**: Select language or use auto-detect
- **Model**: Choose model size (tiny to large)
- **Export Formats**: Select output formats (TXT, SRT, VTT, JSON)

### 3. Start Processing

Click "Start Transcription" to queue the batch job. The system will:
1. Create a job ID
2. Queue tasks for each file
3. Process files in parallel (4 concurrent)
4. Update progress in real-time

### 4. Monitor Progress

The BatchJobList component shows:
- Job status (pending, processing, completed, failed)
- Progress percentage
- Current file being processed
- Start/completion timestamps

### 5. Download Results

Once completed, click download buttons for each format:
- **TXT**: Plain text with segment timestamps
- **SRT**: Subtitle format for video players
- **VTT**: WebVTT format for HTML5 video
- **JSON**: Full data with confidence scores and metadata

## Export Format Examples

### TXT Format
```
=== example.mp3 ===

This is the full transcription text.

--- Segments ---

[00:00:00.000 --> 00:00:05.000]
This is the first segment.

[00:00:05.000 --> 00:00:10.000]
This is the second segment.
```

### SRT Format
```
1
00:00:00,000 --> 00:00:05,000
This is the first segment.

2
00:00:05,000 --> 00:00:10,000
This is the second segment.
```

### VTT Format
```
WEBVTT

00:00:00.000 --> 00:00:05.000
This is the first segment.

00:00:05.000 --> 00:00:10.000
This is the second segment.
```

### JSON Format
```json
{
  "version": "1.0",
  "format": "RTSTT Batch Transcription",
  "total_files": 1,
  "successful_files": 1,
  "results": [
    {
      "file_name": "example.mp3",
      "success": true,
      "text": "Full transcription...",
      "language": "en",
      "confidence": 0.95,
      "duration": 10.0,
      "segments": [
        {
          "start": 0.0,
          "end": 5.0,
          "text": "This is the first segment.",
          "confidence": 0.96
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Celery Worker Not Starting

1. Check Redis is running: `redis-cli -p 6380 ping`
2. Verify environment variables in `.env.local`
3. Check worker logs for errors

### Upload Fails

1. Verify file format is supported
2. Check file size < 500MB
3. Ensure backend is running on port 8001
4. Check FastAPI logs for errors

### Transcription Fails

1. Verify Whisper model is installed
2. Check Celery worker logs
3. Ensure enough disk space in `/tmp/uploads/`
4. Verify Redis connection

### Job Status Not Updating

1. Check frontend polling interval (2 seconds)
2. Verify Redis contains job metadata
3. Check browser console for errors
4. Ensure backend API is accessible

## Performance Tips

1. **Parallel Processing**: System processes 4 files simultaneously
2. **Model Selection**: Use smaller models (tiny/base) for faster processing
3. **File Format**: WAV files process faster than compressed formats
4. **Redis Memory**: Monitor Redis memory usage for large batches

## Development

### Adding New Export Format

1. Add formatter function in `exporters.py`:
```python
def export_to_custom(results, output_path):
    # Implementation
    pass
```

2. Register in `export_transcription()`:
```python
exporters = {
    "custom": export_to_custom,
}
```

3. Add to frontend format selector

### Customizing Celery Workers

Edit `celery_app.py` to adjust:
- Concurrency level
- Task timeout
- Result TTL
- Queue names

## Security Considerations

1. **File Validation**: All uploads are validated for type and size
2. **Temporary Storage**: Files stored in `/tmp/uploads/` with unique IDs
3. **Result TTL**: Job results expire after 24 hours
4. **CORS**: Configure allowed origins in production

## Production Deployment

1. Use dedicated Redis instance
2. Configure Celery with supervisord or systemd
3. Set up file cleanup cron job
4. Monitor Celery worker health
5. Configure CORS for specific origins
6. Use production-grade storage (S3, etc.)

## License

This feature is part of the RTSTT project.
