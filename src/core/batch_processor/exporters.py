"""
Transcription Export Formatters
Export transcription results to various formats: TXT, SRT, VTT, JSON
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

# Export directory
EXPORT_DIR = Path("/tmp/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def format_timestamp_srt(seconds: float) -> str:
    """
    Format timestamp for SRT format (HH:MM:SS,mmm).

    Args:
        seconds: Timestamp in seconds

    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """
    Format timestamp for VTT format (HH:MM:SS.mmm).

    Args:
        seconds: Timestamp in seconds

    Returns:
        Formatted timestamp string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((td.total_seconds() % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def export_to_txt(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Export transcription to plain text format with timestamps.

    Args:
        results: List of transcription results
        output_path: Output file path

    Returns:
        True if successful
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                if not result.get("success", False):
                    f.write(f"[ERROR] {result.get('file_name', 'Unknown')}: {result.get('error', 'Unknown error')}\n\n")
                    continue

                # Write file header
                f.write(f"=== {result.get('file_name', 'Unknown')} ===\n\n")

                # Write full text if available
                if result.get("text"):
                    f.write(result["text"])
                    f.write("\n\n")

                # Write segments with timestamps
                segments = result.get("segments", [])
                if segments:
                    f.write("--- Segments ---\n\n")
                    for seg in segments:
                        start = seg.get("start", 0.0)
                        end = seg.get("end", 0.0)
                        text = seg.get("text", "").strip()

                        f.write(f"[{format_timestamp_vtt(start)} --> {format_timestamp_vtt(end)}]\n")
                        f.write(f"{text}\n\n")

                f.write("\n")

        logger.info(f"Exported to TXT: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to TXT: {e}")
        return False


def export_to_srt(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Export transcription to SRT (SubRip) subtitle format.

    Args:
        results: List of transcription results
        output_path: Output file path

    Returns:
        True if successful
    """
    try:
        subtitle_index = 1

        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                if not result.get("success", False):
                    continue

                segments = result.get("segments", [])

                # If no segments, create one from full text
                if not segments and result.get("text"):
                    f.write(f"{subtitle_index}\n")
                    f.write(f"00:00:00,000 --> 00:00:05,000\n")
                    f.write(f"{result['text']}\n\n")
                    subtitle_index += 1
                    continue

                # Write segments
                for seg in segments:
                    start = seg.get("start", 0.0)
                    end = seg.get("end", 0.0)
                    text = seg.get("text", "").strip()

                    if not text:
                        continue

                    f.write(f"{subtitle_index}\n")
                    f.write(f"{format_timestamp_srt(start)} --> {format_timestamp_srt(end)}\n")
                    f.write(f"{text}\n\n")

                    subtitle_index += 1

        logger.info(f"Exported to SRT: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to SRT: {e}")
        return False


def export_to_vtt(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Export transcription to WebVTT subtitle format.

    Args:
        results: List of transcription results
        output_path: Output file path

    Returns:
        True if successful
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # VTT header
            f.write("WEBVTT\n\n")

            for result in results:
                if not result.get("success", False):
                    continue

                # Add file separator comment
                f.write(f"NOTE {result.get('file_name', 'Unknown')}\n\n")

                segments = result.get("segments", [])

                # If no segments, create one from full text
                if not segments and result.get("text"):
                    f.write(f"00:00:00.000 --> 00:00:05.000\n")
                    f.write(f"{result['text']}\n\n")
                    continue

                # Write segments
                for seg in segments:
                    start = seg.get("start", 0.0)
                    end = seg.get("end", 0.0)
                    text = seg.get("text", "").strip()

                    if not text:
                        continue

                    f.write(f"{format_timestamp_vtt(start)} --> {format_timestamp_vtt(end)}\n")
                    f.write(f"{text}\n\n")

        logger.info(f"Exported to VTT: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to VTT: {e}")
        return False


def export_to_json(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Export transcription to JSON format with full metadata.

    Args:
        results: List of transcription results
        output_path: Output file path

    Returns:
        True if successful
    """
    try:
        export_data = {
            "version": "1.0",
            "format": "RTSTT Batch Transcription",
            "total_files": len(results),
            "successful_files": sum(1 for r in results if r.get("success", False)),
            "failed_files": sum(1 for r in results if not r.get("success", False)),
            "results": results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported to JSON: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False


async def export_transcription(
    job_id: str,
    results: List[Dict[str, Any]],
    format: str
) -> Optional[str]:
    """
    Export transcription results to specified format.

    Args:
        job_id: Job ID for filename
        results: List of transcription results
        format: Export format (txt, srt, vtt, json)

    Returns:
        Path to exported file or None if failed
    """
    if not results:
        logger.warning(f"No results to export for job {job_id}")
        return None

    # Determine output file
    output_path = EXPORT_DIR / f"{job_id}.{format}"

    # Export based on format
    exporters = {
        "txt": export_to_txt,
        "srt": export_to_srt,
        "vtt": export_to_vtt,
        "json": export_to_json
    }

    exporter = exporters.get(format.lower())
    if not exporter:
        logger.error(f"Unknown export format: {format}")
        return None

    success = exporter(results, output_path)

    if success and output_path.exists():
        return str(output_path)

    return None


# Export
__all__ = [
    "export_transcription",
    "export_to_txt",
    "export_to_srt",
    "export_to_vtt",
    "export_to_json",
]
