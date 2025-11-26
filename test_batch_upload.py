#!/usr/bin/env python3
"""
Test script for audio file upload and batch transcription
"""

import os
import time
import requests
import json
from pathlib import Path

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
TEST_AUDIO_DIR = Path(__file__).parent / "tests" / "audio_samples"


def create_test_audio_file():
    """Create a simple test audio file using Python."""
    try:
        import numpy as np
        import soundfile as sf

        # Create test directory
        TEST_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

        # Generate 5 seconds of simple audio (sine wave)
        sample_rate = 16000
        duration = 5
        frequency = 440  # A4 note

        t = np.linspace(0, duration, sample_rate * duration)
        audio = np.sin(2 * np.pi * frequency * t) * 0.3

        # Save as WAV file
        test_file = TEST_AUDIO_DIR / "test_audio.wav"
        sf.write(test_file, audio, sample_rate)

        print(f"✓ Created test audio file: {test_file}")
        return test_file

    except ImportError:
        print("Warning: soundfile and numpy not available, skipping test file creation")
        return None


def test_health_check():
    """Test backend health endpoint."""
    print("\n1. Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend is healthy")
            print(f"  Version: {data.get('version')}")
            print(f"  Connections: {data.get('connections')}")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        return False


def test_upload_file(file_path):
    """Test file upload endpoint."""
    print(f"\n2. Testing file upload...")

    if not file_path or not file_path.exists():
        print("✗ Test file not found, skipping upload test")
        return None

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/wav')}
            response = requests.post(
                f"{BACKEND_URL}/api/upload",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✓ File uploaded successfully")
                print(f"  File ID: {data.get('file_id')}")
                print(f"  Size: {data.get('file_size')} bytes")
                return data.get('file_id')
            else:
                print(f"✗ Upload failed: {data}")
                return None
        else:
            print(f"✗ Upload request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None


def test_start_transcription(file_ids):
    """Test batch transcription start."""
    print(f"\n3. Testing batch transcription...")

    if not file_ids:
        print("✗ No file IDs to transcribe, skipping")
        return None

    try:
        payload = {
            "file_ids": file_ids,
            "provider": "whisper",
            "language": None,  # auto-detect
            "model": "tiny",  # Use tiny for faster testing
            "export_formats": ["txt", "json"]
        }

        response = requests.post(
            f"{BACKEND_URL}/api/batch/transcribe",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✓ Batch transcription started")
                print(f"  Job ID: {data.get('job_id')}")
                print(f"  Files: {data.get('file_count')}")
                return data.get('job_id')
            else:
                print(f"✗ Transcription start failed: {data}")
                return None
        else:
            print(f"✗ Transcription request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None

    except Exception as e:
        print(f"✗ Transcription error: {e}")
        return None


def test_job_status(job_id, max_wait=120):
    """Test job status polling."""
    print(f"\n4. Testing job status polling...")

    if not job_id:
        print("✗ No job ID to check, skipping")
        return False

    start_time = time.time()
    last_status = None

    try:
        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{BACKEND_URL}/api/batch/status/{job_id}",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)

                if status != last_status:
                    print(f"  Status: {status} ({progress:.1f}%)")
                    last_status = status

                if status == 'completed':
                    print(f"✓ Job completed successfully")
                    print(f"  Files processed: {data.get('files_processed')}/{data.get('total_files')}")
                    return True
                elif status == 'failed':
                    print(f"✗ Job failed: {data.get('error')}")
                    return False

                time.sleep(2)  # Poll every 2 seconds
            else:
                print(f"✗ Status check failed: {response.status_code}")
                return False

        print(f"✗ Timeout waiting for job completion")
        return False

    except Exception as e:
        print(f"✗ Status polling error: {e}")
        return False


def test_download_result(job_id):
    """Test downloading transcription results."""
    print(f"\n5. Testing result download...")

    if not job_id:
        print("✗ No job ID to download, skipping")
        return False

    formats = ['txt', 'json']
    success = True

    for fmt in formats:
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/batch/download/{job_id}/{fmt}",
                timeout=10
            )

            if response.status_code == 200:
                # Save to file
                output_file = Path(f"test_output_{job_id}.{fmt}")
                with open(output_file, 'wb') as f:
                    f.write(response.content)

                print(f"✓ Downloaded {fmt.upper()} format: {output_file}")
            else:
                print(f"✗ Download {fmt} failed: {response.status_code}")
                success = False

        except Exception as e:
            print(f"✗ Download {fmt} error: {e}")
            success = False

    return success


def main():
    """Run all tests."""
    print("=" * 60)
    print("Audio File Upload & Batch Transcription Test Suite")
    print("=" * 60)

    # Test 1: Health check
    if not test_health_check():
        print("\n✗ Backend is not accessible. Please start the backend server.")
        return

    # Test 2: Create test file
    test_file = create_test_audio_file()

    # Test 3: Upload file
    file_id = test_upload_file(test_file)
    if not file_id:
        print("\n✗ Upload test failed. Please check the logs.")
        return

    # Test 4: Start transcription
    job_id = test_start_transcription([file_id])
    if not job_id:
        print("\n✗ Transcription start failed. Please check Celery worker is running.")
        return

    # Test 5: Monitor job status
    if not test_job_status(job_id):
        print("\n✗ Job processing failed or timed out.")
        return

    # Test 6: Download results
    if not test_download_result(job_id):
        print("\n✗ Download test failed.")
        return

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
