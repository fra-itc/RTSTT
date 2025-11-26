# STT Benchmarking - Quick Start Guide

## Installation

```bash
cd /home/frisco/projects/RTSTT-model-bench
source venv/bin/activate
pip install faster-whisper psutil python-Levenshtein soundfile
```

## Quick Commands

```bash
# List all providers
python scripts/run_benchmarks.py --list

# Run examples
python examples/benchmark_example.py

# Create test dataset
python scripts/create_test_dataset.py

# Run quick benchmark
python scripts/run_benchmarks.py --quick

# Run full benchmark
python scripts/run_benchmarks.py --full --dataset my_test --parallel
```

## Files Overview

**Core:** `/home/frisco/projects/RTSTT-model-bench/src/core/benchmarks/`
**Scripts:** `/home/frisco/projects/RTSTT-model-bench/scripts/`
**Results:** `/home/frisco/projects/RTSTT-model-bench/benchmarks/results/`
**Docs:** `/home/frisco/projects/RTSTT-model-bench/STT_BENCHMARK_IMPLEMENTATION_SUMMARY.md`

## 11 Providers Supported

**Local (FREE):**
1. Whisper Large-v3 ✓
2. Voxtral Mini 3B
3. NVIDIA Parakeet 0.6B
4. WhisperLiveKit
5. Vosk Lightweight
6. RealtimeSTT

**Cloud ($):**
7. OpenAI Whisper ✓
8. Deepgram Nova-3
9. AssemblyAI Universal-2
10. Mistral Voxtral
11. Google/Azure

✓ = Fully implemented

## Metrics Collected

- **Accuracy:** WER, CER, confidence
- **Speed:** RTFx, latency (p50/p95/p99), throughput
- **Resources:** GPU memory, CPU%, RAM
- **Cost:** $/min, $/hour, break-even
- **Score:** 0-10 weighted overall score

## Report Formats

- HTML (interactive charts)
- Markdown (documentation)
- CSV (raw data)
- JSON (structured)
- SQLite (historical tracking)

## Next Steps

1. Create test audio files
2. Run `python scripts/create_test_dataset.py`
3. Run `python scripts/run_benchmarks.py --quick`
4. View reports in `benchmarks/results/reports/`
