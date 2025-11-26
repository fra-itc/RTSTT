"""
File Upload Handler for Audio Batch Processing
Handles audio file uploads, validation, and batch transcription job management.
"""

import os
import uuid
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import aiofiles

from src.core.batch_processor.audio_processor import queue_batch_transcription, get_job_status, get_job_result
from src.core.batch_processor.exporters import export_transcription


# Configure logging
logger = logging.getLogger(__name__)

# Upload directory configuration
UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# File validation constants
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg",      # MP3
    "audio/mp3",       # MP3 (alternative)
    "audio/wav",       # WAV
    "audio/x-wav",     # WAV (alternative)
    "audio/wave",      # WAV (alternative)
    "audio/flac",      # FLAC
    "audio/x-flac",    # FLAC (alternative)
    "audio/ogg",       # OGG
    "audio/x-ogg",     # OGG (alternative)
    "audio/mp4",       # M4A
    "audio/x-m4a",     # M4A (alternative)
}

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".mp4"}


# Pydantic models
class UploadResponse(BaseModel):
    """Response for file upload."""
    success: bool = Field(..., description="Upload success status")
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Server file path")
    upload_timestamp: str = Field(..., description="Upload timestamp")


class BatchTranscriptionRequest(BaseModel):
    """Request to start batch transcription."""
    file_ids: List[str] = Field(..., description="List of file IDs to transcribe")
    provider: str = Field(default="whisper", description="STT provider to use")
    language: Optional[str] = Field(default=None, description="Language code (e.g., 'en', 'es')")
    model: Optional[str] = Field(default="base", description="Model size (tiny, base, small, medium, large)")
    export_formats: List[str] = Field(default=["txt"], description="Export formats (txt, srt, vtt, json)")


class BatchTranscriptionResponse(BaseModel):
    """Response for batch transcription request."""
    success: bool = Field(..., description="Request success status")
    job_id: str = Field(..., description="Unique job identifier")
    file_count: int = Field(..., description="Number of files in batch")
    estimated_duration: Optional[float] = Field(None, description="Estimated duration in seconds")
    status: str = Field(..., description="Initial job status")


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status (pending, processing, completed, failed)")
    progress: float = Field(..., description="Progress percentage (0-100)")
    files_processed: int = Field(..., description="Number of files processed")
    total_files: int = Field(..., description="Total number of files")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    started_at: Optional[str] = Field(None, description="Job start timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class JobResultResponse(BaseModel):
    """Response for job result retrieval."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    results: List[Dict[str, Any]] = Field(..., description="Transcription results")
    total_duration: Optional[float] = Field(None, description="Total processing duration")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")


# Create router
router = APIRouter(prefix="/api", tags=["File Upload"])


def validate_audio_file(filename: str, content_type: Optional[str]) -> bool:
    """
    Validate audio file by extension and content type.

    Args:
        filename: Original filename
        content_type: MIME content type

    Returns:
        True if valid, False otherwise
    """
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False

    # Check content type if provided
    if content_type and content_type not in SUPPORTED_AUDIO_FORMATS:
        # Try to guess from extension
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type and guessed_type in SUPPORTED_AUDIO_FORMATS:
            return True
        return False

    return True


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload audio file",
    description="Upload an audio file for batch transcription (MP3, WAV, FLAC, OGG, M4A)"
)
async def upload_audio_file(
    file: UploadFile = File(..., description="Audio file to upload")
) -> UploadResponse:
    """
    Upload an audio file for processing.

    Args:
        file: Audio file (max 500MB)

    Returns:
        UploadResponse with file metadata

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file type
    if not validate_audio_file(file.filename, file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix.lower()
    server_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / server_filename

    # Save file with size validation
    file_size = 0
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)

                # Check size limit
                if file_size > MAX_FILE_SIZE:
                    # Clean up partial file
                    await f.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
                    )

                await f.write(chunk)

        logger.info(f"Uploaded file: {file.filename} ({file_size} bytes) -> {file_id}")

        return UploadResponse(
            success=True,
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            file_path=str(file_path),
            upload_timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        # Clean up on error
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post(
    "/batch/transcribe",
    response_model=BatchTranscriptionResponse,
    summary="Start batch transcription",
    description="Queue audio files for batch transcription"
)
async def start_batch_transcription(
    request: BatchTranscriptionRequest
) -> BatchTranscriptionResponse:
    """
    Start batch transcription of uploaded files.

    Args:
        request: Batch transcription configuration

    Returns:
        BatchTranscriptionResponse with job details

    Raises:
        HTTPException: If files not found or validation fails
    """
    # Validate file IDs
    file_paths = []
    for file_id in request.file_ids:
        # Find file with this ID (check all supported extensions)
        found = False
        for ext in SUPPORTED_EXTENSIONS:
            file_path = UPLOAD_DIR / f"{file_id}{ext}"
            if file_path.exists():
                file_paths.append(str(file_path))
                found = True
                break

        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}"
            )

    try:
        # Queue batch transcription job
        job_id = await queue_batch_transcription(
            file_paths=file_paths,
            provider=request.provider,
            language=request.language,
            model=request.model,
            export_formats=request.export_formats
        )

        logger.info(f"Started batch transcription job: {job_id} ({len(file_paths)} files)")

        return BatchTranscriptionResponse(
            success=True,
            job_id=job_id,
            file_count=len(file_paths),
            estimated_duration=None,  # Could calculate based on file sizes
            status="pending"
        )

    except Exception as e:
        logger.error(f"Error starting batch transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch transcription: {str(e)}"
        )


@router.get(
    "/batch/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of a batch transcription job"
)
async def get_batch_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a batch transcription job.

    Args:
        job_id: Job identifier

    Returns:
        JobStatusResponse with current status

    Raises:
        HTTPException: If job not found
    """
    try:
        status_data = await get_job_status(job_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )

        return JobStatusResponse(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get(
    "/batch/result/{job_id}",
    response_model=JobResultResponse,
    summary="Get job result",
    description="Get the transcription results for a completed job"
)
async def get_batch_result(job_id: str) -> JobResultResponse:
    """
    Get the results of a completed batch transcription job.

    Args:
        job_id: Job identifier

    Returns:
        JobResultResponse with transcription results

    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        result_data = await get_job_result(job_id)

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )

        if result_data.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job not completed yet. Current status: {result_data.get('status')}"
            )

        return JobResultResponse(**result_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job result: {str(e)}"
        )


@router.get(
    "/batch/download/{job_id}/{format}",
    summary="Download transcription",
    description="Download transcription in specified format (txt, srt, vtt, json)"
)
async def download_transcription(
    job_id: str,
    format: str
) -> FileResponse:
    """
    Download transcription result in specified format.

    Args:
        job_id: Job identifier
        format: Export format (txt, srt, vtt, json)

    Returns:
        FileResponse with transcription file

    Raises:
        HTTPException: If job not found, not completed, or format invalid
    """
    # Validate format
    valid_formats = ["txt", "srt", "vtt", "json"]
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Supported: {', '.join(valid_formats)}"
        )

    try:
        # Get job result
        result_data = await get_job_result(job_id)

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}"
            )

        if result_data.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job not completed yet. Current status: {result_data.get('status')}"
            )

        # Export to requested format
        export_file = await export_transcription(
            job_id=job_id,
            results=result_data.get("results", []),
            format=format.lower()
        )

        if not export_file or not Path(export_file).exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate export file"
            )

        # Determine media type
        media_types = {
            "txt": "text/plain",
            "srt": "text/plain",
            "vtt": "text/vtt",
            "json": "application/json"
        }

        return FileResponse(
            path=export_file,
            media_type=media_types.get(format.lower(), "application/octet-stream"),
            filename=f"transcription_{job_id}.{format.lower()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download transcription: {str(e)}"
        )


# Export router
__all__ = ["router"]
