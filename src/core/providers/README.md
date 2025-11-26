# Provider Abstraction Layer

This module provides a unified interface for different service providers (STT, NLP, Summary) supporting both local and cloud implementations.

## Architecture

```
providers/
├── base.py              # Abstract base classes and interfaces
├── exceptions.py        # Provider-specific exceptions
├── factory.py           # Provider factory for instantiation
├── selector.py          # Intelligent provider selection
├── local/               # Local provider implementations
│   ├── whisper_local.py
│   ├── voxtral_mini.py
│   ├── parakeet_tdt.py
│   ├── vosk.py
│   └── ...
└── cloud/               # Cloud provider implementations
    ├── openai.py
    ├── openrouter.py
    ├── deepgram.py
    ├── assemblyai.py
    └── ...
```

## Key Concepts

### Provider Types

- **Local**: Runs on-premise, no API costs, requires GPU/CPU resources
- **Cloud**: API-based, pay-per-use, no local resources needed
- **Hybrid**: Can run in either mode

### Provider Capabilities

Providers declare their capabilities:
- `STREAMING_STT` - Real-time streaming transcription
- `BATCH_STT` - Batch file transcription
- `MULTILINGUAL` - Supports multiple languages
- `KEYWORD_EXTRACTION` - Extract keywords from text
- `SENTIMENT_ANALYSIS` - Analyze sentiment
- `ABSTRACTIVE_SUMMARY` - Generate abstractive summaries
- And more...

### Selection Criteria

The `ProviderSelector` chooses the best provider based on:
- **Required capabilities** - Must support needed features
- **Performance** - Latency, accuracy, error rate
- **Cost** - Optimize for lowest cost if specified
- **Availability** - Provider health and uptime
- **Priority** - User-configured preferences

## Usage Examples

### Creating Providers

```python
from src.core.providers import ProviderFactory, ProviderConfig, ProviderType

# Create factory
factory = ProviderFactory()

# Register providers
from src.core.providers.local.whisper_local import WhisperLocalProvider
factory.register_stt_provider("whisper-local", WhisperLocalProvider)

# Create provider instance
config = ProviderConfig(
    name="whisper-local",
    provider_type=ProviderType.LOCAL,
    priority=100,
    max_retries=3,
    extra_config={
        "model_size": "large-v3",
        "device": "cuda"
    }
)

provider = await factory.create_stt_provider(config)
```

### Using Provider Selector

```python
from src.core.providers import ProviderSelector, SelectionCriteria, ProviderCapability

selector = ProviderSelector(factory)

# Define selection criteria
criteria = SelectionCriteria(
    required_capabilities=[ProviderCapability.STREAMING_STT],
    max_latency_ms=500,
    optimize_for_cost=True,
    prefer_local=True
)

# Select best provider
providers = [provider1, provider2, provider3]
best_provider = await selector.select_stt_provider(providers, criteria)

# Use the selected provider
result = await best_provider.transcribe(audio_data, sample_rate=16000, language="it")
print(f"Transcription: {result.text}")
print(f"Confidence: {result.confidence}")
```

### Transcription with Fallback

```python
# Create fallback chain
fallback_chain = await selector.create_fallback_chain(
    provider_names=["whisper-local", "openai-whisper", "deepgram-nova3"],
    service_type="stt"
)

# Try providers in order
result = None
for provider in fallback_chain:
    try:
        result = await provider.transcribe(audio_data, sample_rate=16000)
        break
    except Exception as e:
        logger.warning(f"Provider {provider.name} failed: {e}")
        continue

if result:
    print(f"Success with {result.provider_name}: {result.text}")
```

### Cost Estimation

```python
# Estimate cost before processing
cost = selector.get_cost_estimate(
    provider=deepgram_provider,
    audio_seconds=300  # 5 minutes
)

print(f"Estimated cost: ${cost:.4f}")

# Choose cheapest provider
providers_with_cost = [
    (p, selector.get_cost_estimate(p, audio_seconds=300))
    for p in available_providers
]
cheapest = min(providers_with_cost, key=lambda x: x[1])
print(f"Cheapest: {cheapest[0].name} (${cheapest[1]:.4f})")
```

## Implementing New Providers

### STT Provider Example

```python
from src.core.providers.base import STTProvider, STTResult, ProviderConfig, ProviderCapability

class MySTTProvider(STTProvider):
    """Custom STT provider implementation."""

    async def initialize(self) -> None:
        """Load model, connect to API, etc."""
        self.model = load_my_model(self.config.extra_config)
        self._is_initialized = True

    async def shutdown(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'model'):
            del self.model
        self._is_initialized = False

    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        try:
            # Test inference or API connection
            return True
        except:
            return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Declare capabilities."""
        return [
            ProviderCapability.BATCH_STT,
            ProviderCapability.MULTILINGUAL,
            ProviderCapability.PUNCTUATION
        ]

    async def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: str = "",
        model: str = "",
        **kwargs
    ) -> STTResult:
        """Perform transcription."""
        # Your implementation here
        text = self.model.transcribe(audio_data)

        return STTResult(
            text=text,
            language=language,
            confidence=0.95,
            provider_name=self.name,
            audio_duration_seconds=len(audio_data) / (sample_rate * 2),
            processing_time_ms=processing_time
        )

    async def transcribe_streaming(self, audio_stream, sample_rate=16000, language="", **kwargs):
        """Streaming transcription (optional)."""
        raise NotImplementedError("Streaming not supported")
```

### Register Your Provider

```python
from src.core.providers.factory import get_factory
from .my_stt_provider import MySTTProvider

factory = get_factory()
factory.register_stt_provider("my-stt", MySTTProvider)
```

## Provider Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Deepgram
DEEPGRAM_API_KEY=...

# OpenRouter
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Configuration File

```yaml
providers:
  stt:
    - name: whisper-local
      type: local
      enabled: true
      priority: 100
      config:
        model_size: large-v3
        device: cuda
        compute_type: float16

    - name: openai-whisper
      type: cloud
      enabled: true
      priority: 50
      api_key: ${OPENAI_API_KEY}
      cost_per_minute: 0.006

    - name: deepgram-nova3
      type: cloud
      enabled: true
      priority: 75
      api_key: ${DEEPGRAM_API_KEY}
      cost_per_minute: 0.0043
```

## Testing Providers

```python
import pytest
from src.core.providers import ProviderConfig, ProviderType
from src.core.providers.local.whisper_local import WhisperLocalProvider

@pytest.mark.asyncio
async def test_whisper_local_transcription():
    config = ProviderConfig(
        name="whisper-local-test",
        provider_type=ProviderType.LOCAL,
        extra_config={"model_size": "base"}
    )

    provider = WhisperLocalProvider(config)
    await provider.initialize()

    # Test transcription
    audio_data = load_test_audio()
    result = await provider.transcribe(audio_data, sample_rate=16000, language="en")

    assert result.text
    assert result.confidence > 0
    assert result.provider_name == "whisper-local-test"

    await provider.shutdown()
```

## Performance Monitoring

Providers automatically track metrics:
- Total requests
- Success/failure rates
- Average latency
- Total cost
- Error rates
- Uptime percentage

Access metrics:
```python
print(f"Provider: {provider.name}")
print(f"Total requests: {provider.metrics.total_requests}")
print(f"Avg latency: {provider.metrics.avg_latency_ms}ms")
print(f"Error rate: {provider.metrics.error_rate}%")
print(f"Total cost: ${provider.metrics.total_cost_usd:.2f}")
```

## References

- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Deepgram Nova-3](https://developers.deepgram.com/docs)
- [AssemblyAI](https://www.assemblyai.com/docs)
- [OpenRouter](https://openrouter.ai/docs)
