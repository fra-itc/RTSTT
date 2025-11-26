# Audio File Upload & Batch Transcription Feature

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements-batch.txt

# Or install individually
pip install celery redis aiofiles python-multipart httpx
```

### 2. Start Services

Open **3 separate terminals**:

**Terminal 1 - Redis Server:**
```bash
redis-server --port 6380
```

**Terminal 2 - Celery Worker:**
```bash
./scripts/start_celery_worker.sh
```

**Terminal 3 - FastAPI Backend:**
```bash
cd /home/frisco/projects/RTSTT-audio-upload
source venv/bin/activate
uvicorn src.agents.orchestrator.fastapi_app:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 4 - Frontend (optional):**
```bash
npm run dev
```

### 3. Test the Feature

```bash
python test_batch_upload.py
```

## Features Implemented

### Backend (FastAPI)

#### File Upload Handler
- **Location**: `src/agents/orchestrator/file_upload_handler.py`
- **Endpoints**:
  - `POST /api/upload` - Upload audio files
  - `POST /api/batch/transcribe` - Start batch transcription
  - `GET /api/batch/status/{job_id}` - Check job status
  - `GET /api/batch/result/{job_id}` - Get results
  - `GET /api/batch/download/{job_id}/{format}` - Download transcription

#### Batch Processor (Celery)
- **Location**: `src/core/batch_processor/`
- **Components**:
  - `celery_app.py` - Celery configuration with Redis
  - `audio_processor.py` - Transcription tasks
  - `exporters.py` - Format converters (TXT/SRT/VTT/JSON)

#### Features:
- Validates audio file formats (MP3, WAV, FLAC, OGG, M4A)
- Maximum file size: 500MB
- Parallel processing: 4 concurrent workers
- Redis-based job queue and status tracking
- Multiple export formats
- Progress tracking and error handling

### Frontend (React + Material-UI)

#### Components Created:

1. **FileDropzone** (`src/ui/desktop/renderer/components/FileDropzone/`)
   - Drag-and-drop file upload
   - File validation
   - Multiple file selection
   - Visual feedback

2. **BatchJobList** (`src/ui/desktop/renderer/components/BatchJobList/`)
   - Real-time job status display
   - Progress bars
   - Expandable job details
   - Download buttons for completed jobs

3. **FileUploadView** (`src/ui/desktop/renderer/views/FileUploadView.tsx`)
   - Complete upload workflow
   - Provider/model/language selection
   - Export format configuration
   - Real-time job monitoring

## API Examples

### Upload File

```bash
curl -X POST http://localhost:8001/api/upload \
  -F "file=@test_audio.mp3"
```

Response:
```json
{
  "success": true,
  "file_id": "abc-123-def",
  "filename": "test_audio.mp3",
  "file_size": 1024000,
  "file_path": "/tmp/uploads/abc-123-def.mp3",
  "upload_timestamp": "2025-11-26T12:00:00Z"
}
```

### Start Batch Transcription

```bash
curl -X POST http://localhost:8001/api/batch/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["abc-123-def"],
    "provider": "whisper",
    "language": "en",
    "model": "base",
    "export_formats": ["txt", "srt", "vtt", "json"]
  }'
```

Response:
```json
{
  "success": true,
  "job_id": "job-456-xyz",
  "file_count": 1,
  "status": "pending"
}
```

### Check Job Status

```bash
curl http://localhost:8001/api/batch/status/job-456-xyz
```

Response:
```json
{
  "job_id": "job-456-xyz",
  "status": "processing",
  "progress": 50.0,
  "files_processed": 0,
  "total_files": 1,
  "current_file": "test_audio.mp3",
  "started_at": "2025-11-26T12:01:00Z"
}
```

### Download Result

```bash
curl http://localhost:8001/api/batch/download/job-456-xyz/txt \
  --output transcription.txt
```

## File Structure

```
RTSTT-audio-upload/
├── src/
│   ├── agents/
│   │   └── orchestrator/
│   │       ├── fastapi_app.py          # Main API (updated)
│   │       └── file_upload_handler.py  # Upload endpoints (NEW)
│   ├── core/
│   │   └── batch_processor/            # (NEW)
│   │       ├── __init__.py
│   │       ├── celery_app.py          # Celery config
│   │       ├── audio_processor.py      # Transcription tasks
│   │       └── exporters.py            # Format exporters
│   └── ui/
│       └── desktop/
│           └── renderer/
│               ├── components/
│               │   ├── FileDropzone/   # (NEW)
│               │   │   ├── FileDropzone.tsx
│               │   │   └── index.ts
│               │   └── BatchJobList/   # (NEW)
│               │       ├── BatchJobList.tsx
│               │       └── index.ts
│               └── views/
│                   └── FileUploadView.tsx  # (NEW)
├── scripts/
│   └── start_celery_worker.sh          # (NEW)
├── requirements-batch.txt               # (NEW)
├── test_batch_upload.py                 # (NEW)
├── AUDIO_FILE_UPLOAD_GUIDE.md          # (NEW)
└── AUDIO_FILE_UPLOAD_README.md         # (NEW)
```

## Architecture Diagram

```
┌─────────────────┐
│   Frontend      │
│  (React + MUI)  │
│                 │
│ FileUploadView  │
│ ├─ FileDropzone │
│ └─ BatchJobList │
└────────┬────────┘
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │
│   Backend       │
│                 │
│ /api/upload     │
│ /api/batch/*    │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼──┐   ┌──▼────┐
│Redis │   │Celery │
│Queue │   │Worker │
│      │   │       │
│Job   │   │Audio  │
│Meta  │   │Proc   │
└──────┘   └───┬───┘
               │
           ┌───▼────┐
           │Whisper │
           │ Model  │
           └────────┘
```

## Workflow

1. **Upload**: User uploads audio files via FileDropzone
2. **Configure**: User selects provider, language, model, formats
3. **Queue**: Files are queued for batch processing
4. **Process**: Celery workers process files in parallel (4 concurrent)
5. **Track**: Real-time status updates via polling
6. **Download**: Results available in multiple formats

## Configuration

### Environment Variables (.env.local)

```bash
# Backend
BACKEND_PORT=8001

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0

# STT Service
STT_SERVICE_HOST=localhost
STT_SERVICE_PORT=50054

# Frontend
VITE_PORT=5174
VITE_BACKEND_URL=http://localhost:8001
```

### Celery Configuration

Edit `src/core/batch_processor/celery_app.py`:

```python
# Worker settings
worker_concurrency=4,              # 4 parallel workers
worker_max_tasks_per_child=50,     # Restart after 50 tasks
task_time_limit=3600,              # 1 hour max per task
task_soft_time_limit=3300,         # 55 minute soft limit
```

## Testing

### Automated Test Suite

```bash
# Run full test suite
python test_batch_upload.py
```

Tests include:
1. Backend health check
2. File upload
3. Batch transcription start
4. Job status polling
5. Result download

### Manual Testing

1. **Upload Test**:
```bash
curl -X POST http://localhost:8001/api/upload \
  -F "file=@test.mp3"
```

2. **Transcribe Test**:
```bash
curl -X POST http://localhost:8001/api/batch/transcribe \
  -H "Content-Type: application/json" \
  -d '{"file_ids":["your-file-id"],"provider":"whisper","model":"tiny"}'
```

3. **Check Status**:
```bash
curl http://localhost:8001/api/batch/status/your-job-id
```

## Troubleshooting

### Issue: Celery worker won't start

**Solution**:
```bash
# Check Redis
redis-cli -p 6380 ping

# Check environment variables
cat .env.local

# Check Python path
which python
```

### Issue: Upload fails with 413 error

**Solution**: File too large (max 500MB)
- Reduce file size
- Or increase limit in `file_upload_handler.py`:
```python
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1GB
```

### Issue: Transcription timeout

**Solution**: Increase time limits
- Edit `celery_app.py`:
```python
task_time_limit=7200,  # 2 hours
```

### Issue: Frontend can't connect to backend

**Solution**:
```bash
# Check backend is running
curl http://localhost:8001/health

# Check CORS settings in fastapi_app.py
# Update VITE_BACKEND_URL in frontend
```

## Performance Tuning

### Increase Parallelism

```python
# celery_app.py
worker_concurrency=8,  # Increase from 4 to 8
```

### Use Faster Model

```python
# In frontend or API request
model="tiny"  # Fastest
model="base"  # Default
model="large" # Most accurate but slowest
```

### Optimize Redis

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
```

## Production Checklist

- [ ] Configure Redis persistence
- [ ] Set up Celery monitoring (Flower)
- [ ] Configure log rotation
- [ ] Set up file cleanup cron job
- [ ] Use production WSGI server (gunicorn)
- [ ] Configure CORS for specific origins
- [ ] Set up HTTPS/SSL
- [ ] Monitor disk space for uploads
- [ ] Configure Celery autoscaling
- [ ] Set up error alerting

## Next Steps

1. **Provider Integration**: Add OpenAI Whisper API, Deepgram
2. **Cost Tracking**: Track API usage and costs
3. **Queue Management**: Add priority queues
4. **Storage**: Integrate S3 for persistent storage
5. **Notifications**: Add email/webhook notifications
6. **Analytics**: Track processing metrics
7. **UI Enhancements**: Add drag-to-reorder, bulk delete
8. **Mobile Support**: Optimize for mobile devices

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in Celery worker
3. Check Redis keys: `redis-cli -p 6380 KEYS "batch_job:*"`
4. Enable debug logging in FastAPI

## License

Part of RTSTT project - Real-Time Speech-to-Text Transcription
