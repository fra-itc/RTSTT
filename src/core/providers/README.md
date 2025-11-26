# External STT Providers

This module provides a unified abstraction layer for multiple Speech-to-Text providers, allowing seamless switching between local and cloud-based STT services.

## Overview

The provider system supports:
- **Local Providers**: Whisper Large-v3 (GPU-based, free)
- **Cloud Providers**: OpenAI, Deepgram, AssemblyAI
- **Automatic Fallback**: Switch to backup providers on failure
- **Cost Tracking**: Monitor usage and costs across providers
- **Streaming Adapter**: Convert batch APIs to pseudo-streaming

## Architecture

```
providers/
├── base.py                  # Abstract base classes
├── factory.py               # Provider creation and registry
├── manager.py               # Provider lifecycle and fallback
├── comparison.py            # Cost and feature comparison
├── local/
│   └── whisper_local.py    # Local Whisper wrapper
├── cloud/
│   ├── openai.py           # OpenAI Whisper API
│   ├── deepgram.py         # Deepgram Nova-2/3
│   └── assemblyai.py       # AssemblyAI Universal-2
└── adapters/
    └── streaming_adapter.py # Batch-to-streaming conversion
```

## Provider Comparison

| Provider | Type | Cost/min | Latency | Streaming | Diarization |
|----------|------|----------|---------|-----------|-------------|
| Local Whisper | Local | Free | 300ms | ✅ | ❌ |
| OpenAI Whisper | Cloud | $0.006 | 2000ms | ❌ | ❌ |
| Deepgram Nova-2 | Cloud | $0.0043 | 50ms | ✅ | ✅ |
| Deepgram Nova-3 | Cloud | $0.0059 | 50ms | ✅ | ✅ |
| AssemblyAI | Cloud | $0.015 | 5000ms | ❌ | ✅ |

## Quick Start

### 1. Create a Provider

```python
from core.providers.factory import ProviderFactory

# Local Whisper (Free, requires GPU)
provider = await ProviderFactory.create_local_whisper(
    model="large-v3",
    language="it"
)

# OpenAI Whisper API
provider = await ProviderFactory.create_openai(
    api_key="sk-...",
    language="it"
)

# Deepgram with streaming
provider = await ProviderFactory.create_deepgram(
    api_key="...",
    model="nova-2",
    enable_diarization=True
)

# AssemblyAI with advanced features
provider = await ProviderFactory.create_assemblyai(
    api_key="...",
    enable_speaker_labels=True,
    enable_sentiment=True
)
```

### 2. Transcribe Audio

```python
# Batch transcription
result = await provider.transcribe(
    audio="path/to/audio.wav",
    language="it"
)

print(result.text)
print(f"Segments: {len(result.segments)}")
print(f"Language: {result.language}")

# Streaming transcription (if supported)
async for partial_result in provider.transcribe_streaming(audio_stream):
    print(f"Partial: {partial_result.text}")
```

### 3. Use Provider Manager (with Fallback)

```python
from core.providers.manager import ProviderManager

# Create manager
manager = ProviderManager()

# Set primary provider with fallback chain
primary = await ProviderFactory.create_local_whisper()
fallback1 = await ProviderFactory.create_deepgram(api_key="...")
fallback2 = await ProviderFactory.create_openai(api_key="...")

await manager.set_primary_provider(
    primary,
    fallback_chain=[fallback1, fallback2]
)

# Transcribe with automatic fallback
result = await manager.transcribe(
    audio="audio.wav",
    use_fallback=True
)

# Get usage statistics
stats = await manager.get_usage_stats()
print(f"Total cost: ${stats['total_cost']:.2f}")
print(f"Total duration: {stats['total_duration_minutes']:.1f} min")
```

## Cost Tracking

```python
# Estimate cost before transcription
cost = await provider.estimate_cost(audio_duration_seconds=300)
print(f"Estimated cost: ${cost:.4f}")

# Get usage report
stats = await manager.get_usage_stats()
print(f"Provider stats: {stats['provider_stats']}")

# Export usage report
manager.export_usage_report("usage_report.json")
```

## Provider Selection

### By Cost

```python
from core.providers.comparison import compare_by_cost

# Compare providers for 60 min/month usage
comparisons = compare_by_cost(duration_minutes=60)
for comp in comparisons:
    print(f"{comp['name']}: ${comp['monthly_cost']:.2f}/month")
```

### By Latency

```python
from core.providers.comparison import compare_by_latency

comparisons = compare_by_latency()
for comp in comparisons:
    print(f"{comp['name']}: {comp['latency_ms']}ms")
```

### By Use Case

```python
from core.providers.comparison import get_best_for_use_case

# Best for real-time transcription
providers = get_best_for_use_case(
    use_case="real-time",
    budget_per_hour=1.0,
    requires_streaming=True,
    requires_diarization=False
)
```

## Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="whisper-1"

# Deepgram
export DEEPGRAM_API_KEY="..."
export DEEPGRAM_MODEL="nova-2"

# AssemblyAI
export ASSEMBLYAI_API_KEY="..."
```

### Create from Environment

```python
# Automatically load from environment variables
provider = await ProviderFactory.create_from_env("openai")
```

## Advanced Features

### Streaming Adapter

Convert batch-only providers to streaming:

```python
from core.providers.adapters import StreamingAdapter

# Wrap batch provider
adapter = StreamingAdapter(
    provider=batch_provider,
    chunk_duration_ms=3000,  # Process every 3 seconds
    overlap_ms=500           # 500ms overlap
)

# Use as streaming provider
async for result in adapter.transcribe_streaming(audio_stream):
    print(f"Partial: {result.text}")
```

### Provider Registry

```python
from core.providers.factory import ProviderRegistry

# Get all available providers
providers = ProviderRegistry.get_available_providers()

# Get or create cached provider
provider = await ProviderRegistry.get_or_create_provider("openai")

# Cleanup all providers
await ProviderRegistry.cleanup_all()
```

### Health Monitoring

```python
# Check single provider
is_healthy = await provider.health_check()

# Check all providers in manager
health_status = await manager.check_all_health()
for name, is_healthy in health_status.items():
    print(f"{name}: {'OK' if is_healthy else 'FAIL'}")
```

## Frontend Integration

### Provider Selector Component

```tsx
import { STTProviderSelector } from '@/components/STTProviderSelector';

<STTProviderSelector
  selectedProvider={currentProvider}
  onProviderChange={handleProviderChange}
  estimatedMinutesPerDay={60}
/>
```

### Configuration Panel

```tsx
import { STTConfigPanel } from '@/components/STTConfigPanel';

<STTConfigPanel
  selectedProvider={currentProvider}
  config={providerConfigs}
  onConfigChange={handleConfigChange}
  onTestConnection={handleTestConnection}
/>
```

### Usage Dashboard

```tsx
import { STTUsageDashboard } from '@/components/STTUsageDashboard';

<STTUsageDashboard />
```

## Best Practices

1. **Use Local Whisper for Development**: Free and no API limits
2. **Use Deepgram for Production**: Best balance of cost, latency, and features
3. **Set Up Fallback Chain**: Primary (local) → Fallback (cloud)
4. **Monitor Costs**: Use ProviderManager to track usage
5. **Test API Keys**: Use health_check() before deployment
6. **Cache Providers**: Use ProviderRegistry for singleton pattern

## Troubleshooting

### Provider Initialization Failed

```python
# Check if provider is initialized
if not provider.is_initialized():
    success = await provider.initialize()
    if not success:
        print("Initialization failed")
```

### API Key Issues

```python
# Verify API key
is_healthy = await provider.health_check()
if not is_healthy:
    print("API key may be invalid")
```

### GPU Not Available (Local Whisper)

```python
import torch
if not torch.cuda.is_available():
    print("CUDA not available. Use cloud provider instead.")
```

## Examples

See `examples/provider_usage_example.py` for complete examples.

## API Reference

### STTProvider (Base Class)

- `async initialize() -> bool`: Initialize provider
- `async transcribe(audio, language, **kwargs) -> STTResult`: Transcribe audio
- `async transcribe_streaming(audio_stream, language, **kwargs) -> AsyncIterator[STTResult]`: Stream transcription
- `get_info() -> ProviderInfo`: Get provider information
- `async health_check() -> bool`: Check provider health
- `async estimate_cost(duration_seconds) -> float`: Estimate cost
- `async cleanup()`: Cleanup resources

### ProviderFactory

- `create_local_whisper(model, language, device)`: Create local Whisper
- `create_openai(api_key, model, language)`: Create OpenAI provider
- `create_deepgram(api_key, model, language, enable_diarization)`: Create Deepgram
- `create_assemblyai(api_key, model, language, enable_speaker_labels)`: Create AssemblyAI
- `create_from_env(provider_name)`: Create from environment variables

### ProviderManager

- `set_primary_provider(provider, fallback_chain)`: Set primary and fallbacks
- `transcribe(audio, language, use_fallback, **kwargs)`: Transcribe with fallback
- `get_usage_stats()`: Get usage statistics
- `estimate_cost(duration_seconds, provider_name)`: Estimate cost
- `check_all_health()`: Check health of all providers
- `switch_provider(provider_name)`: Switch to different provider
- `export_usage_report(filepath)`: Export usage to JSON

## License

Part of the RTSTT project. See main LICENSE file.
