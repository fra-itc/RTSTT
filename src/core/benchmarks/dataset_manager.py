"""
Dataset Manager for STT benchmarking.

Manages test datasets with ground truth transcriptions for accuracy evaluation.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import wave
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioSample:
    """
    A single audio sample with ground truth transcription.
    """
    audio_path: Path
    transcription: str  # Ground truth
    language: str  # ISO 639-1 code (e.g., "en", "it")
    duration_seconds: float
    sample_rate: int
    speaker: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DatasetManager:
    """
    Manages test datasets for STT benchmarking.

    Supports:
    - Custom test sets with known transcriptions
    - Audio preprocessing (resample, format conversion)
    - Dataset splitting (train/val/test)
    - Ground truth management
    """

    def __init__(self, dataset_root: Path):
        """
        Initialize DatasetManager.

        Args:
            dataset_root: Root directory for datasets
        """
        self.dataset_root = Path(dataset_root)
        self.dataset_root.mkdir(parents=True, exist_ok=True)

        self.datasets: Dict[str, List[AudioSample]] = {}
        logger.info(f"DatasetManager initialized at {self.dataset_root}")

    def load_dataset(
        self,
        dataset_name: str,
        metadata_path: Optional[Path] = None
    ) -> List[AudioSample]:
        """
        Load a dataset from disk.

        Expected structure:
        dataset_root/
          {dataset_name}/
            audio/
              sample1.wav
              sample2.wav
            metadata.json  # Contains transcriptions and metadata

        Args:
            dataset_name: Name of the dataset
            metadata_path: Optional path to metadata JSON

        Returns:
            List[AudioSample]: Loaded audio samples
        """
        dataset_dir = self.dataset_root / dataset_name

        if not dataset_dir.exists():
            logger.warning(f"Dataset {dataset_name} not found at {dataset_dir}")
            return []

        # Load metadata
        if metadata_path is None:
            metadata_path = dataset_dir / "metadata.json"

        if not metadata_path.exists():
            logger.error(f"Metadata file not found: {metadata_path}")
            return []

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load audio samples
        samples = []
        audio_dir = dataset_dir / "audio"

        for item in metadata.get("samples", []):
            audio_file = audio_dir / item["filename"]

            if not audio_file.exists():
                logger.warning(f"Audio file not found: {audio_file}")
                continue

            # Get audio duration
            duration, sample_rate = self._get_audio_info(audio_file)

            sample = AudioSample(
                audio_path=audio_file,
                transcription=item["transcription"],
                language=item.get("language", "en"),
                duration_seconds=duration,
                sample_rate=sample_rate,
                speaker=item.get("speaker"),
                metadata=item.get("metadata", {})
            )
            samples.append(sample)

        self.datasets[dataset_name] = samples
        logger.info(f"Loaded {len(samples)} samples from dataset '{dataset_name}'")

        return samples

    def create_dataset(
        self,
        dataset_name: str,
        samples: List[Dict],
        copy_audio: bool = False
    ) -> List[AudioSample]:
        """
        Create a new dataset.

        Args:
            dataset_name: Name for the new dataset
            samples: List of sample dicts with keys:
                - audio_path: Path to audio file
                - transcription: Ground truth text
                - language: Language code
                - speaker: Optional speaker ID
            copy_audio: Whether to copy audio files to dataset directory

        Returns:
            List[AudioSample]: Created samples
        """
        dataset_dir = self.dataset_root / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)

        audio_dir = dataset_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        created_samples = []
        metadata_list = []

        for i, sample_data in enumerate(samples):
            source_path = Path(sample_data["audio_path"])

            if not source_path.exists():
                logger.warning(f"Audio file not found: {source_path}")
                continue

            # Copy or reference audio file
            if copy_audio:
                dest_path = audio_dir / f"sample_{i:04d}{source_path.suffix}"
                import shutil
                shutil.copy2(source_path, dest_path)
                audio_path = dest_path
            else:
                audio_path = source_path

            # Get audio info
            duration, sample_rate = self._get_audio_info(audio_path)

            sample = AudioSample(
                audio_path=audio_path,
                transcription=sample_data["transcription"],
                language=sample_data.get("language", "en"),
                duration_seconds=duration,
                sample_rate=sample_rate,
                speaker=sample_data.get("speaker"),
                metadata=sample_data.get("metadata", {})
            )
            created_samples.append(sample)

            # Add to metadata
            metadata_list.append({
                "filename": audio_path.name if copy_audio else str(audio_path),
                "transcription": sample.transcription,
                "language": sample.language,
                "duration_seconds": sample.duration_seconds,
                "sample_rate": sample.sample_rate,
                "speaker": sample.speaker,
                "metadata": sample.metadata
            })

        # Save metadata
        metadata = {
            "dataset_name": dataset_name,
            "sample_count": len(created_samples),
            "samples": metadata_list
        }

        metadata_path = dataset_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.datasets[dataset_name] = created_samples
        logger.info(f"Created dataset '{dataset_name}' with {len(created_samples)} samples")

        return created_samples

    def get_dataset(self, dataset_name: str) -> List[AudioSample]:
        """
        Get a loaded dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List[AudioSample]: Dataset samples
        """
        return self.datasets.get(dataset_name, [])

    def split_dataset(
        self,
        dataset_name: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        shuffle: bool = True
    ) -> Tuple[List[AudioSample], List[AudioSample], List[AudioSample]]:
        """
        Split dataset into train/val/test sets.

        Args:
            dataset_name: Name of the dataset
            train_ratio: Ratio for training set
            val_ratio: Ratio for validation set
            test_ratio: Ratio for test set
            shuffle: Whether to shuffle before splitting

        Returns:
            Tuple of (train, val, test) sample lists
        """
        samples = self.get_dataset(dataset_name)

        if not samples:
            logger.warning(f"Dataset '{dataset_name}' is empty")
            return [], [], []

        # Validate ratios
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
            raise ValueError("Split ratios must sum to 1.0")

        # Shuffle if requested
        if shuffle:
            import random
            samples = samples.copy()
            random.shuffle(samples)

        # Calculate split indices
        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_samples = samples[:train_end]
        val_samples = samples[train_end:val_end]
        test_samples = samples[val_end:]

        logger.info(
            f"Split dataset '{dataset_name}': "
            f"train={len(train_samples)}, val={len(val_samples)}, test={len(test_samples)}"
        )

        return train_samples, val_samples, test_samples

    def filter_by_language(
        self,
        dataset_name: str,
        language: str
    ) -> List[AudioSample]:
        """
        Filter dataset by language.

        Args:
            dataset_name: Name of the dataset
            language: ISO 639-1 language code

        Returns:
            List[AudioSample]: Filtered samples
        """
        samples = self.get_dataset(dataset_name)
        filtered = [s for s in samples if s.language == language]

        logger.info(
            f"Filtered dataset '{dataset_name}' by language '{language}': "
            f"{len(filtered)}/{len(samples)} samples"
        )

        return filtered

    def get_statistics(self, dataset_name: str) -> Dict:
        """
        Get dataset statistics.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dict with statistics
        """
        samples = self.get_dataset(dataset_name)

        if not samples:
            return {"error": "Dataset is empty"}

        total_duration = sum(s.duration_seconds for s in samples)
        languages = {}
        speakers = {}

        for sample in samples:
            languages[sample.language] = languages.get(sample.language, 0) + 1
            if sample.speaker:
                speakers[sample.speaker] = speakers.get(sample.speaker, 0) + 1

        return {
            "dataset_name": dataset_name,
            "sample_count": len(samples),
            "total_duration_seconds": total_duration,
            "total_duration_hours": total_duration / 3600,
            "avg_duration_seconds": total_duration / len(samples),
            "languages": languages,
            "speaker_count": len(speakers),
            "speakers": speakers,
        }

    def _get_audio_info(self, audio_path: Path) -> Tuple[float, int]:
        """
        Get audio duration and sample rate.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (duration_seconds, sample_rate)
        """
        try:
            with wave.open(str(audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration, rate
        except Exception as e:
            logger.warning(f"Could not read audio file {audio_path}: {e}")
            # Try with numpy/soundfile as fallback
            try:
                import soundfile as sf
                info = sf.info(str(audio_path))
                return info.duration, info.samplerate
            except:
                return 0.0, 16000  # Default values

    def list_datasets(self) -> List[str]:
        """
        List all available datasets.

        Returns:
            List of dataset names
        """
        datasets = [d.name for d in self.dataset_root.iterdir() if d.is_dir()]
        logger.info(f"Found {len(datasets)} datasets: {datasets}")
        return datasets
