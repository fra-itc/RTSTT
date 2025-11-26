#!/usr/bin/env python3
"""
Create a test dataset for STT benchmarking.

This script helps you create a test dataset with audio files and ground truth transcriptions.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.benchmarks import DatasetManager

def create_sample_dataset():
    """Create a sample test dataset."""

    # Initialize dataset manager
    project_root = Path(__file__).parent.parent
    dataset_root = project_root / "benchmarks" / "datasets"
    dataset_manager = DatasetManager(dataset_root)

    # Sample dataset metadata
    # Replace these with actual audio files and transcriptions
    samples = [
        {
            "audio_path": str(dataset_root / "audio_samples" / "sample1.wav"),
            "transcription": "The quick brown fox jumps over the lazy dog.",
            "language": "en",
            "speaker": "speaker1",
            "metadata": {
                "source": "test",
                "quality": "high"
            }
        },
        {
            "audio_path": str(dataset_root / "audio_samples" / "sample2.wav"),
            "transcription": "Speech recognition technology has advanced significantly.",
            "language": "en",
            "speaker": "speaker1"
        },
        {
            "audio_path": str(dataset_root / "audio_samples" / "sample3.wav"),
            "transcription": "Real-time transcription requires low latency processing.",
            "language": "en",
            "speaker": "speaker2"
        },
    ]

    # Create dataset
    print("Creating sample test dataset...")

    try:
        created_samples = dataset_manager.create_dataset(
            dataset_name="quick_test",
            samples=samples,
            copy_audio=False  # Set to True to copy audio files to dataset directory
        )

        print(f"✓ Created dataset with {len(created_samples)} samples")
        print(f"  Dataset location: {dataset_root / 'quick_test'}")

        # Show statistics
        stats = dataset_manager.get_statistics("quick_test")
        print("\nDataset Statistics:")
        print(f"  Total samples: {stats['sample_count']}")
        print(f"  Total duration: {stats['total_duration_seconds']:.1f} seconds")
        print(f"  Languages: {stats['languages']}")

    except Exception as e:
        print(f"✗ Failed to create dataset: {e}")
        print("\nNote: Make sure you have actual audio files at the specified paths.")
        print("You can modify the 'samples' list above to point to your audio files.")


def create_dataset_from_directory():
    """Create a dataset from a directory of audio files."""

    print("\nCreate Dataset from Directory")
    print("=" * 60)

    audio_dir = input("Enter path to directory containing audio files: ").strip()
    audio_dir = Path(audio_dir)

    if not audio_dir.exists():
        print(f"✗ Directory not found: {audio_dir}")
        return

    # Find audio files
    audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))

    if not audio_files:
        print(f"✗ No audio files found in {audio_dir}")
        return

    print(f"Found {len(audio_files)} audio files")

    # Create metadata file template
    metadata_template = {
        "dataset_name": "my_dataset",
        "samples": []
    }

    for audio_file in audio_files:
        metadata_template["samples"].append({
            "filename": audio_file.name,
            "transcription": "TODO: Add transcription here",
            "language": "en",
            "speaker": "unknown"
        })

    # Save template
    output_path = audio_dir / "metadata_template.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_template, f, indent=2)

    print(f"\n✓ Created metadata template: {output_path}")
    print("\nNext steps:")
    print("1. Edit the metadata file to add transcriptions for each audio file")
    print("2. Save the file as 'metadata.json'")
    print("3. Run this script again to import the dataset")


def main():
    print("STT Benchmark Dataset Creator")
    print("=" * 60)
    print()
    print("Options:")
    print("1. Create sample test dataset")
    print("2. Create dataset from directory")
    print("3. Exit")
    print()

    choice = input("Enter your choice (1-3): ").strip()

    if choice == "1":
        create_sample_dataset()
    elif choice == "2":
        create_dataset_from_directory()
    elif choice == "3":
        print("Exiting...")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
