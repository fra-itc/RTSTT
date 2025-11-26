# Quick Start: External LLM APIs

Get up and running with OpenAI and OpenRouter integration in 5 minutes.

## Prerequisites

- Python 3.9+
- RTSTT backend installed
- (Optional) OpenAI API key
- (Optional) OpenRouter API key

## Step 1: Install Dependencies

```bash
cd /home/frisco/projects/RTSTT-external-llm
pip install -r requirements-external-llm.txt
```

This installs:
- `aiohttp` - HTTP client for API calls
- `cryptography` - API key encryption

## Step 2: Run Setup Script

```bash
python scripts/setup_external_llm.py
```

This interactive script will:
1. Check dependencies
2. Guide you through API key setup
3. Test provider connectivity
4. Generate a setup report

### Adding API Keys

When prompted, choose option 1 or 2:

**Option 1: OpenAI**
```
Enter OpenAI API key: sk-proj-your-key-here
```

**Option 2: OpenRouter**
```
Enter OpenRouter API key: sk-or-v1-your-key-here
```

### Alternative: Environment Variables

Add to your `.env` file:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

## Step 3: Test Providers

```bash
python tests/test_providers.py
```

This will:
- Test invalid key handling (should fail gracefully)
- Test NLP analysis with configured providers
- Test summary generation
- Test cost tracking

## Step 4: Use in Your Code

### Python Backend

```python
from src.agents.orchestrator.provider_integration import get_provider_orchestrator

# Initialize
orchestrator = get_provider_orchestrator()
await orchestrator.initialize()

# Analyze text with OpenAI
result, error = await orchestrator.analyze_text(
    text="Apple Inc. CEO Tim Cook announced new products today.",
    provider_name="openai-gpt4"
)

print(f"Keywords: {result.keywords}")
print(f"Entities: {result.entities}")
print(f"Sentiment: {result.sentiment}")
print(f"Cost: ${result.metadata['cost_usd']:.6f}")

# Summarize with OpenRouter (Claude)
result, error = await orchestrator.summarize_text(
    text="Long text to summarize...",
    provider_name="openrouter",
    style="concise"
)

print(f"Summary: {result.summary}")
print(f"Key Points: {result.key_points}")
print(f"Cost: ${result.metadata['cost_usd']:.6f}")

# Get cost statistics
stats = orchestrator.get_cost_stats("daily")
print(f"Total cost today: ${stats['total_cost']:.6f}")
```

### Frontend Integration

#### 1. API Settings Page

```typescript
import APISettingsPanel from './components/APISettingsPanel/APISettingsPanel';

function SettingsPage() {
  const handleSaveKey = async (provider: string, key: string) => {
    const response = await fetch('/api/config/api-key', {
      method: 'POST',
      body: JSON.stringify({ provider, key }),
    });
  };

  const handleTestConnection = async (provider: string) => {
    const response = await fetch(`/api/providers/test/${provider}`);
    return response.ok;
  };

  return (
    <APISettingsPanel
      onSaveKey={handleSaveKey}
      onTestConnection={handleTestConnection}
    />
  );
}
```

#### 2. Provider Selection

```typescript
import ProviderSelector from './components/ProviderSelector/ProviderSelector';

function MainApp() {
  const [providers, setProviders] = useState({ nlp: [], summary: [] });

  useEffect(() => {
    fetch('/api/providers/available')
      .then(res => res.json())
      .then(data => setProviders(data));
  }, []);

  const handleNLPChange = (providerId: string) => {
    // Update selected provider
  };

  return (
    <ProviderSelector
      nlpProviders={providers.nlp}
      summaryProviders={providers.summary}
      onNLPProviderChange={handleNLPChange}
      onSummaryProviderChange={handleSummaryChange}
    />
  );
}
```

#### 3. Cost Monitoring

```typescript
import CostMonitor from './components/CostMonitor/CostMonitor';

function CostDashboard() {
  const [stats, setStats] = useState(null);

  const fetchStats = async (timeRange: string) => {
    const response = await fetch(`/api/costs/stats?range=${timeRange}`);
    const data = await response.json();
    setStats(data);
  };

  return (
    <CostMonitor
      stats={stats}
      onTimeRangeChange={fetchStats}
      onRefresh={() => fetchStats('daily')}
      onExport={() => {/* Export logic */}}
    />
  );
}
```

## Step 5: Start Services

```bash
# Terminal 1: Backend
cd /home/frisco/projects/RTSTT-external-llm
python src/agents/orchestrator/fastapi_app.py --port 8002

# Terminal 2: Frontend
npm run dev -- --port 5175

# Terminal 3: Redis (if not running)
redis-server --port 6381
```

## Usage Examples

### Example 1: Basic NLP Analysis

```python
import asyncio
from src.agents.orchestrator.provider_integration import get_provider_orchestrator

async def main():
    orchestrator = get_provider_orchestrator()
    await orchestrator.initialize()

    result, error = await orchestrator.analyze_text(
        "The stock market reached new heights today."
    )

    if error:
        print(f"Error: {error}")
    else:
        print(f"Sentiment: {result.sentiment}")

asyncio.run(main())
```

### Example 2: Custom Model Selection

```python
# Use specific OpenRouter model
result, error = await orchestrator.analyze_text(
    text="Sample text",
    provider_name="openrouter",
    model="meta-llama/llama-3.1-70b-instruct"  # Override default
)
```

### Example 3: Fallback to Local

```python
# Automatically falls back to local if API fails
result, error = await orchestrator.analyze_text(
    text="Sample text",
    provider_name="openai-gpt4",
    fallback_to_local=True  # Default: True
)

if result.metadata.get('fallback'):
    print("Used local fallback due to API error")
```

## Cost Management

### Check Available Budget

```python
stats = orchestrator.get_cost_stats("monthly")
print(f"This month: ${stats['total_cost']:.2f}")

# Set alerts (implement in your app)
if stats['total_cost'] > 100.0:
    send_alert("Monthly budget exceeded!")
```

### Export Cost Report

```python
import json
from datetime import datetime

stats = orchestrator.get_cost_stats("monthly")
report = {
    "generated_at": datetime.now().isoformat(),
    "period": "monthly",
    **stats
}

with open("cost_report.json", "w") as f:
    json.dump(report, f, indent=2)
```

## Troubleshooting

### "ProviderAuthenticationError: Invalid API key"
- Check API key format (OpenAI: `sk-...`, OpenRouter: `sk-or-...`)
- Verify key is valid on provider's website
- Ensure key has sufficient permissions

### "ProviderQuotaExceededError: Rate limit exceeded"
- Wait and retry (automatic exponential backoff)
- Check your API plan limits
- Consider upgrading plan or using different provider

### "Provider not available"
- Run `python scripts/setup_external_llm.py` to check status
- Verify API key is configured
- Test connectivity with test script

### Cost tracking not working
- Ensure orchestrator is initialized: `await orchestrator.initialize()`
- Check that providers are returning metadata with cost info
- Verify cost entries: `orchestrator.cost_entries`

## Best Practices

1. **Always use fallback**: Keep `fallback_to_local=True` for reliability
2. **Monitor costs**: Check `get_cost_stats()` regularly
3. **Secure keys**: Never commit API keys to git
4. **Test first**: Use setup script before production
5. **Handle errors**: Always check error returns
6. **Cache results**: Implement caching for repeated requests (future)
7. **Set budgets**: Monitor spending and set alerts

## Next Steps

1. ✅ Configure API keys
2. ✅ Test providers
3. ✅ Integrate UI components
4. ✅ Set up cost monitoring
5. ⬜ Deploy to production
6. ⬜ Monitor costs in production
7. ⬜ Optimize based on usage patterns

## API Reference

See `EXTERNAL_LLM_IMPLEMENTATION.md` for:
- Complete API documentation
- Detailed architecture
- All configuration options
- Advanced usage examples

## Support

- Documentation: `EXTERNAL_LLM_IMPLEMENTATION.md`
- Tests: `tests/test_providers.py`
- Setup: `scripts/setup_external_llm.py`
- Issues: Create issue in repository
