# STT Model Benchmarking Framework

Comprehensive benchmarking system for comparing 11 different Speech-to-Text models.

## Quick Start

```bash
# List available providers
python scripts/run_benchmarks.py --list

# Run quick test
python scripts/run_benchmarks.py --quick

# Run full benchmark
python scripts/run_benchmarks.py --full --dataset my_test --parallel
```

## Supported Providers

**Local Models (6):**
1. Whisper Large-v3 (FREE)
2. Voxtral Mini 3B (FREE)
3. NVIDIA Parakeet 0.6B (FREE)
4. WhisperLiveKit (FREE)
5. Vosk Lightweight (FREE)
6. RealtimeSTT (FREE)

**Cloud APIs (5):**
1. OpenAI Whisper ($0.006/min)
2. Deepgram Nova-3 ($0.0043/min)
3. AssemblyAI Universal-2 ($0.15/hr)
4. Mistral Voxtral ($0.005/min)
5. Google/Azure ($0.004-0.017/min)

## Metrics Collected

- **Accuracy**: WER, CER, confidence scores
- **Performance**: RTFx, latency (p50/p95/p99), throughput
- **Resources**: GPU memory, CPU%, RAM
- **Cost**: Per minute, per hour, break-even analysis
- **Overall Score**: 0-10 weighted score

## Architecture

See `/home/frisco/projects/RTSTT-model-bench/src/core/benchmarks/` for implementation details.
