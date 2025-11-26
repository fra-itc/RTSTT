"""
Audio Batch Processor
Celery tasks for processing audio files in batch mode.
"""

import os
import uuid
import json
import logging
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import redis
import httpx
from celery import group

from .celery_app import celery_app

# Configure logging
logger = logging.getLogger(__name__)

# Redis client for job metadata
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# STT Service configuration
STT_SERVICE_HOST = os.getenv("STT_SERVICE_HOST", "localhost")
STT_SERVICE_PORT = int(os.getenv("STT_SERVICE_PORT", "50054"))

# Job status constants
JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"


def get_redis_key(job_id: str, suffix: str = "") -> str:
    """Generate Redis key for job data."""
    if suffix:
        return f"batch_job:{job_id}:{suffix}"
    return f"batch_job:{job_id}"


async def queue_batch_transcription(
    file_paths: List[str],
    provider: str = "whisper",
    language: Optional[str] = None,
    model: str = "base",
    export_formats: List[str] = None
) -> str:
    """
    Queue a batch of audio files for transcription.

    Args:
        file_paths: List of audio file paths
        provider: STT provider to use
        language: Language code
        model: Model size
        export_formats: List of export formats

    Returns:
        Job ID
    """
    if export_formats is None:
        export_formats = ["txt"]

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Store job metadata in Redis
    job_metadata = {
        "job_id": job_id,
        "status": JOB_STATUS_PENDING,
        "file_count": len(file_paths),
        "files_processed": 0,
        "total_files": len(file_paths),
        "progress": 0.0,
        "current_file": None,
        "started_at": None,
        "completed_at": None,
        "error": None,
        "provider": provider,
        "language": language,
        "model": model,
        "export_formats": export_formats,
        "file_paths": file_paths,
        "results": []
    }

    redis_client.setex(
        get_redis_key(job_id),
        3600 * 24,  # 24 hour TTL
        json.dumps(job_metadata)
    )

    # Queue Celery tasks
    logger.info(f"Queueing batch job {job_id} with {len(file_paths)} files")

    # Create group of tasks for parallel processing
    job = group(
        transcribe_audio_file.s(
            job_id=job_id,
            file_path=file_path,
            file_index=idx,
            provider=provider,
            language=language,
            model=model
        )
        for idx, file_path in enumerate(file_paths)
    )

    # Apply async
    result = job.apply_async()

    logger.info(f"Batch job {job_id} queued successfully")

    return job_id


@celery_app.task(bind=True, name="transcribe_audio_file")
def transcribe_audio_file(
    self,
    job_id: str,
    file_path: str,
    file_index: int,
    provider: str = "whisper",
    language: Optional[str] = None,
    model: str = "base"
) -> Dict[str, Any]:
    """
    Celery task to transcribe a single audio file.

    Args:
        job_id: Batch job ID
        file_path: Path to audio file
        file_index: Index in batch
        provider: STT provider
        language: Language code
        model: Model size

    Returns:
        Transcription result dictionary
    """
    logger.info(f"Processing file {file_index} in job {job_id}: {file_path}")

    try:
        # Update job status
        _update_job_progress(job_id, file_index, Path(file_path).name)

        # Read audio file
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        with open(file_path, "rb") as f:
            audio_data = f.read()

        logger.info(f"Read audio file: {len(audio_data)} bytes")

        # Call STT service (using local Whisper model for now)
        result = _transcribe_with_whisper(
            audio_data=audio_data,
            file_path=file_path,
            language=language,
            model=model
        )

        # Prepare result
        transcription_result = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "file_index": file_index,
            "success": True,
            "text": result.get("text", ""),
            "language": result.get("language", language or "auto"),
            "confidence": result.get("confidence", 0.0),
            "duration": result.get("duration", 0.0),
            "segments": result.get("segments", []),
            "provider": provider,
            "model": model,
            "processed_at": datetime.utcnow().isoformat()
        }

        # Store result in Redis
        _store_file_result(job_id, file_index, transcription_result)

        logger.info(f"Successfully transcribed file {file_index} in job {job_id}")

        return transcription_result

    except Exception as e:
        logger.error(f"Error transcribing file {file_index} in job {job_id}: {e}", exc_info=True)

        # Store error result
        error_result = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "file_index": file_index,
            "success": False,
            "error": str(e),
            "processed_at": datetime.utcnow().isoformat()
        }

        _store_file_result(job_id, file_index, error_result)

        # Update job with error
        _update_job_error(job_id, str(e))

        # Re-raise for Celery retry mechanism
        raise


def _transcribe_with_whisper(
    audio_data: bytes,
    file_path: str,
    language: Optional[str] = None,
    model: str = "base"
) -> Dict[str, Any]:
    """
    Transcribe audio using local Whisper model.

    Args:
        audio_data: Audio file bytes
        file_path: Path to audio file
        language: Language code
        model: Model size

    Returns:
        Transcription result
    """
    try:
        import whisper
        import tempfile
        import numpy as np

        logger.info(f"Loading Whisper model: {model}")

        # Load model (cached after first load)
        whisper_model = whisper.load_model(model)

        # Transcribe directly from file path (Whisper handles audio loading)
        logger.info(f"Transcribing audio file: {file_path}")

        result = whisper_model.transcribe(
            file_path,
            language=language,
            task="transcribe",
            verbose=False
        )

        # Extract segments with timing
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": seg.get("text", "").strip(),
                "confidence": seg.get("no_speech_prob", 0.0)  # Whisper uses no_speech_prob
            })

        transcription = {
            "text": result.get("text", "").strip(),
            "language": result.get("language", language or "auto"),
            "segments": segments,
            "duration": segments[-1]["end"] if segments else 0.0,
            "confidence": 1.0 - np.mean([s.get("no_speech_prob", 0) for s in result.get("segments", [])]) if result.get("segments") else 0.0
        }

        logger.info(f"Transcription complete: {len(segments)} segments, {transcription['duration']:.2f}s")

        return transcription

    except ImportError:
        logger.error("Whisper not installed. Install with: pip install openai-whisper")
        raise Exception("Whisper model not available")
    except Exception as e:
        logger.error(f"Error transcribing with Whisper: {e}")
        raise


def _update_job_progress(job_id: str, file_index: int, current_file: str):
    """Update job progress in Redis."""
    try:
        key = get_redis_key(job_id)
        job_data = redis_client.get(key)

        if job_data:
            metadata = json.loads(job_data)

            # Update progress
            metadata["files_processed"] = file_index
            metadata["current_file"] = current_file
            metadata["progress"] = (file_index / metadata["total_files"]) * 100

            if metadata["status"] == JOB_STATUS_PENDING:
                metadata["status"] = JOB_STATUS_PROCESSING
                metadata["started_at"] = datetime.utcnow().isoformat()

            redis_client.setex(key, 3600 * 24, json.dumps(metadata))

    except Exception as e:
        logger.error(f"Error updating job progress: {e}")


def _store_file_result(job_id: str, file_index: int, result: Dict[str, Any]):
    """Store file transcription result in Redis."""
    try:
        key = get_redis_key(job_id)
        job_data = redis_client.get(key)

        if job_data:
            metadata = json.loads(job_data)

            # Add result
            metadata["results"].append(result)
            metadata["files_processed"] = len(metadata["results"])
            metadata["progress"] = (len(metadata["results"]) / metadata["total_files"]) * 100

            # Check if job is complete
            if len(metadata["results"]) >= metadata["total_files"]:
                metadata["status"] = JOB_STATUS_COMPLETED
                metadata["completed_at"] = datetime.utcnow().isoformat()
                metadata["current_file"] = None

            redis_client.setex(key, 3600 * 24, json.dumps(metadata))

    except Exception as e:
        logger.error(f"Error storing file result: {e}")


def _update_job_error(job_id: str, error: str):
    """Update job with error status."""
    try:
        key = get_redis_key(job_id)
        job_data = redis_client.get(key)

        if job_data:
            metadata = json.loads(job_data)

            # Only mark as failed if no successful results yet
            if not metadata.get("results"):
                metadata["status"] = JOB_STATUS_FAILED
                metadata["completed_at"] = datetime.utcnow().isoformat()

            # Store error but allow job to continue
            if not metadata.get("errors"):
                metadata["errors"] = []
            metadata["errors"].append(error)

            redis_client.setex(key, 3600 * 24, json.dumps(metadata))

    except Exception as e:
        logger.error(f"Error updating job error: {e}")


async def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a batch job.

    Args:
        job_id: Job ID

    Returns:
        Job status dictionary or None if not found
    """
    try:
        key = get_redis_key(job_id)
        job_data = redis_client.get(key)

        if not job_data:
            return None

        metadata = json.loads(job_data)

        return {
            "job_id": job_id,
            "status": metadata["status"],
            "progress": metadata["progress"],
            "files_processed": metadata["files_processed"],
            "total_files": metadata["total_files"],
            "current_file": metadata.get("current_file"),
            "started_at": metadata.get("started_at"),
            "completed_at": metadata.get("completed_at"),
            "error": metadata.get("error")
        }

    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return None


async def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the full results of a completed batch job.

    Args:
        job_id: Job ID

    Returns:
        Job results dictionary or None if not found
    """
    try:
        key = get_redis_key(job_id)
        job_data = redis_client.get(key)

        if not job_data:
            return None

        metadata = json.loads(job_data)

        # Calculate total duration
        total_duration = 0
        if metadata.get("started_at") and metadata.get("completed_at"):
            start = datetime.fromisoformat(metadata["started_at"])
            end = datetime.fromisoformat(metadata["completed_at"])
            total_duration = (end - start).total_seconds()

        return {
            "job_id": job_id,
            "status": metadata["status"],
            "results": metadata.get("results", []),
            "total_duration": total_duration,
            "completed_at": metadata.get("completed_at"),
            "provider": metadata.get("provider"),
            "language": metadata.get("language"),
            "model": metadata.get("model")
        }

    except Exception as e:
        logger.error(f"Error getting job result: {e}")
        return None


# Export
__all__ = [
    "queue_batch_transcription",
    "get_job_status",
    "get_job_result",
    "transcribe_audio_file"
]
