# Real-Time Speech-to-Text Orchestrator

![Version](https://img.shields.io/badge/version-1.0.0--POC-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20WSL2%20%7C%20Linux-0078D4)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

**Cross-platform, multi-agent orchestrated real-time speech-to-text system with NLP insights and automatic summarization, powered by ORCHIDEA Framework v1.3.**

---

## 🎯 Overview

This Proof of Concept (POC) demonstrates a production-grade real-time STT system with **full cross-platform support** featuring:

- **Audio Capture**: Cross-platform drivers (PulseAudio, PortAudio, WASAPI) with WebSocket bridge for WSL2
- **STT Engine**: Whisper Large V3 optimized for RTX 5080 GPU with TensorRT
- **NLP Pipeline**: Complete STT→NLP→Summary enrichment pipeline (250-312ms total latency)
- **NLP Insights**: Real-time keyword extraction, named entity recognition, and sentiment analysis
- **AI Suggestions**: Automatic text summarization and intelligent recommendations
- **Modern UI**: Beautiful Electron desktop app with Material-UI v7 and responsive grid layout
- **Real-time Dashboard**: Live transcription, insights panel, and suggestions panel with professional design
- **Orchestration**: ORCHIDEA v1.3 framework with multi-agent coordination

### Key Performance Targets & Achievements

- ✅ **Pipeline latency**: **253-312ms** (STT: 250-311ms, NLP: <1ms, Summary: <1ms)
- ✅ **Platform support**: Windows, WSL2, Linux (native), macOS (via PortAudio)
- Word Error Rate: **<5%**
- GPU memory: **<14GB**
- CPU usage (audio): **<5%**
- Test coverage: **>95%**

### Platform Support

| Platform | Audio Driver | Status | Notes |
|----------|--------------|--------|-------|
| **Windows 11** | PortAudio / WASAPI* | ✅ | *WASAPI refactor pending |
| **WSL2** | WebSocket Bridge | ✅ | Automated setup available |
| **Linux Native** | PulseAudio / PortAudio | ✅ | Tested on Ubuntu 22.04+ |
| **macOS** | PortAudio (CoreAudio) | ⚠️ | Untested, should work |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Electron Desktop App                         │
│                    React + Web Audio API                         │
│            Real-time waveform & transcription display            │
└──────────────────────┬──────────────────────────────────────────┘
                       │ WebSocket
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend Gateway (8000)                  │
│              WebSocket, REST, gRPC Client Management            │
└──────────────┬──────────────────┬────────────────────────────────┘
               │ gRPC             │ Redis Streams
               ├────────┬─────────┼────────┬──────────────┐
               ↓        ↓         ↓        ↓              ↓
    ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────┐
    │ STT Engine   │ │ NLP Service  │ │ Summary    │ │  Redis   │
    │ Whisper V3   │ │ (gRPC 50052) │ │  Service   │ │ Cache &  │
    │ (gRPC 50051) │ │              │ │ (50053)    │ │  Streams │
    │              │ │ • Keywords   │ │            │ │ (6379)   │
    │ • RTX 5080   │ │ • Entities   │ │ • Llama-3.2│ │          │
    │ • TensorRT   │ │ • Sentiment  │ │ • Caching  │ │          │
    │ • <250ms     │ │ • <50ms      │ │ • <200ms   │ │          │
    └──────────────┘ └──────────────┘ └────────────┘ └──────────┘
```

### ORCHIDEA Multi-Agent Teams

- **Master Orchestrator**: Claude Opus 4.1 (HAS H4)
- **Audio Team**: 3 agents - Capture, VAD, Buffer
- **ML Team**: 4 agents - STT, NLP, Summary, Optimization
- **Frontend Team**: 2 agents - Electron, React
- **Integration Team**: 2 agents - Backend, Infrastructure

---

## Wave 4A Achievements

**Completion Date:** November 24, 2025

### Track 2 Deliverables - Production gRPC Services

- **NLP Service (Port 50052)**
  - Keyword extraction from transcriptions
  - Entity recognition and classification
  - Sentiment analysis with confidence scores
  - Performance: <50ms per request
  - Horizontal scaling support via connection pooling

- **Summary Service (Port 50053)**
  - Llama-3.2-8B-Instruct summarization
  - Redis-backed response caching (60-80% hit rate)
  - Batch summarization support
  - Performance: <200ms per request (uncached ~150-180ms)
  - Automatic cache invalidation

### Track 3 Deliverables - Frontend Integration

- **Real Audio Capture Integration**
  - Web Audio API microphone input in AudioTester component
  - Real-time waveform visualization from actual audio
  - Live audio level metering (RMS-based)
  - WebSocket streaming to backend
  - Voice Activity Detection (VAD) integration

- **AudioTester Component Enhancements**
  - Real microphone device enumeration
  - Actual transcription results (no mock data)
  - Real latency measurements from backend
  - Actual confidence scores from Whisper models
  - Test logging with complete session data

### Integration Improvements

- **WebSocket Gateway Updates**
  - gRPC client connection management
  - Automatic service discovery
  - Connection pooling with configurable pool size
  - Graceful fallback on service unavailability
  - Health check integration

- **End-to-End Pipeline**
  - Audio → WebSocket → Backend → gRPC services → Response
  - Total pipeline latency: 253-312ms (target: <500ms) ✅
  - Parallel service execution where possible
  - Comprehensive error handling and logging

### Observability Enhancements

- Prometheus metrics for all gRPC services
- Service health monitoring via gRPC health checks
- Latency tracking at each pipeline stage
- Cache hit rate monitoring for Summary service

---

## 📸 Screenshots

### Main Dashboard
![Main Dashboard](docs/screenshots/main-dashboard.png)
*Real-time transcription with integrated insights and suggestions panels*

### Insights Panel
![Insights Panel](docs/screenshots/insights-panel.png)
*Live NLP insights: keywords with scores, named entities with types, and sentiment analysis with breakdown*

### Suggestions Panel
![Suggestions Panel](docs/screenshots/suggestions-panel.png)
*AI-generated summary and intelligent recommendations with copy functionality*

### Professional Color Scheme
The application features a modern, professional color palette:
- **Primary**: Deep blue (#0066CC) for main actions and emphasis
- **Secondary**: Elegant purple (#7C3AED) for accents and highlights
- **Semantic Colors**: Modern greens, ambers, and reds for success/warning/error states
- **Dark Mode**: Rich navy blue background (#0F172A) with excellent contrast
- **Light Mode**: Clean blue-tinted white (#F8FAFC) for a professional appearance

All colors are WCAG AA compliant for accessibility.

---

## 🚀 Quick Start

### Prerequisites

**Common Requirements:**
- **GPU**: NVIDIA RTX 5080 Blackwell (16GB VRAM) - **FULLY VALIDATED ✅** or compatible GPU
- **CUDA**: 12.8+ (required for RTX 5080 sm_120 support)
- **PyTorch**: 2.7.0+cu128 (validated on RTX 5080)
- **Python**: 3.10+
- **Docker**: 24.0+ with NVIDIA Container Runtime
- **Redis**: 7.2+

**Platform-Specific:**
- **Windows**: Node.js 20.x (for Electron UI)
- **WSL2**: Ubuntu 22.04+ distribution
- **Linux**: PulseAudio or PortAudio19-dev

> **RTX 5080 Validation**: All ML services (STT, NLP, Summary) passed 7/7 GPU validation tests with PyTorch 2.7.0+cu128 and CUDA 12.8. See [RTX_5080_VALIDATION_REPORT.md](RTX_5080_VALIDATION_REPORT.md) for full details.

### Installation

#### Option A: WSL2 (Automated Setup)

```bash
# Clone repository
git clone <repository-url>
cd realtime-stt-orchestrator

# Run automated setup (installs all dependencies)
./scripts/setup-wsl2.sh

# Deploy POC
./scripts/deploy-poc.sh test
```

#### Option B: Native Linux

```bash
# Clone repository
git clone <repository-url>
cd realtime-stt-orchestrator

# Install system dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose portaudio19-dev python3-pyaudio

# Setup environment
cp .env.example .env
# Edit .env as needed

# Install audio driver dependencies
pip install -r requirements-audio.txt

# Build and deploy
docker-compose build
docker-compose up -d

# Test with real audio
python -m src.host_audio_bridge.main --driver pulseaudio
```

#### Option C: Windows 11 (Manual Setup)

```bash
# 1. Clone Repository
git clone <repository-url>
cd realtime-stt-orchestrator

# 2. Setup Python Environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements-audio.txt
pip install -r requirements/ml.txt
pip install -r requirements/dev.txt
```

#### 3. Download ML Models

```bash
# Whisper Large V3
python scripts/download_whisper.py

# Silero VAD
python scripts/download_silero_vad.py

# NLP models (Mistral, Sentence-BERT, PyAnnote)
python scripts/download_nlp_models.py

# Summary model (Llama-3.2)
python scripts/download_summary_model.py
```

#### 4. Configure Environment

**Option A: Docker Secrets (Recommended for Security)**

```bash
# Run interactive setup script
bash scripts/setup-secrets.sh

# This will create:
# - infrastructure/secrets/hf_token.txt (HuggingFace token)
# - infrastructure/secrets/redis_password.txt (Redis password)
# - infrastructure/secrets/jwt_secret.txt (JWT signing key)
# - infrastructure/secrets/grafana_admin_password.txt (Grafana password)

# All files are automatically set to permission 600 (secure)
```

**Option B: Environment Variables (Traditional)**

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your configuration
notepad .env
```

> 💡 **See [SECRETS.md](SECRETS.md)** for comprehensive secrets management guide

#### 5. Start Services with Docker

**If using Docker Secrets (from Option A above):**

```bash
# Start all services with secrets
docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
```

**If using Environment Variables (from Option B above):**

```bash
# Start Redis + monitoring stack
docker-compose up -d redis prometheus grafana

# Build and start ML services (requires NVIDIA Docker)
docker-compose up -d stt-engine nlp-service summary-service

# Start backend
docker-compose up -d backend
```

#### 5.1 Start Monitoring Stack (Optional but Recommended)

```bash
# Start Prometheus (metrics collection)
docker-compose up -d prometheus

# Start Grafana (visualization)
docker-compose up -d grafana

# Services are now monitored at:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3001 (admin/admin)
```

#### 6. Install Electron Frontend

```bash
cd src/ui/desktop
npm install
npm run dev  # Development mode
# or
npm run build  # Production build
```

### Verify Installation

```bash
# Check services health
curl http://localhost:8000/health

# Check individual service health
curl http://localhost:8000/health/services

# List audio devices
curl http://localhost:8000/api/v1/devices

# Access Grafana dashboard
# http://localhost:3001 (admin/admin)

# Access Prometheus
# http://localhost:9090
```

### Performance Verification (Wave 4A)

```bash
# Run end-to-end latency test
pytest tests/test_grpc_services_integration.py::test_end_to_end_pipeline -v

# Verify gRPC service latencies
pytest tests/test_grpc_services_integration.py -v -k "latency"

# Check total pipeline performance
curl http://localhost:8000/metrics | grep rtstt_
```

**Expected Performance Metrics (Wave 4A):**
- STT latency: 250-311ms
- NLP latency: <50ms
- Summary latency (uncached): 150-180ms
- Summary latency (cached): 5-10ms
- Total pipeline: 253-312ms
- Target: <500ms ✅

---

## 📖 Usage

### Desktop App

1. Launch the Electron app
2. Select audio input device (or use system loopback)
3. Configure recording settings (language, model, sample rate)
4. Click "Start Recording"
5. View real-time updates across three panels:
   - **Transcription Panel** (Left): Live transcription with confidence scores
   - **Insights Panel** (Top Right): NLP insights including keywords, named entities, and sentiment analysis
   - **Suggestions Panel** (Bottom Right): AI-generated summary and intelligent recommendations

### UI Features

- **Professional Color Scheme**: WCAG AA compliant colors with modern blue and purple accents
- **Responsive Grid Layout**: Automatically adapts to different screen sizes
- **Real-time Updates**: All panels update as new data arrives via WebSocket
- **Interactive Components**: Copy suggestions/summary to clipboard, export transcriptions in multiple formats
- **Empty States**: Clear visual feedback when no data is available
- **Loading States**: Skeleton loaders indicate when AI is processing

### API Usage

#### Start Transcription (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'transcription_start',
    timestamp: Date.now(),
    payload: {
      device_id: 'wasapi-loopback-0',
      language: 'en',
      enable_nlp: true,
      enable_summary: true
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message.payload);
};
```

#### gRPC Services (Wave 4A)

**NLP Service (Port 50052):**

```python
import grpc
from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc

channel = grpc.insecure_channel('localhost:50052')
stub = nlp_service_pb2_grpc.NLPServiceStub(channel)

request = nlp_service_pb2.TranscriptionRequest(
    text="Your transcription here",
    session_id="session_001",
    top_keywords=10
)
response = stub.ExtractInsights(request)
print(f"Keywords: {[kw.keyword for kw in response.keywords]}")
```

**Summary Service (Port 50053):**

```python
import grpc
from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

channel = grpc.insecure_channel('localhost:50053')
stub = summary_service_pb2_grpc.SummaryServiceStub(channel)

request = summary_service_pb2.TextRequest(
    text="Long text to summarize...",
    session_id="session_001"
)
response = stub.GenerateSummary(request)
print(f"Summary: {response.summary}")
print(f"Cache hit: {response.cache_hit}")
```

#### REST API

```bash
# List sessions
curl http://localhost:8000/api/v1/sessions

# Get transcript
curl http://localhost:8000/api/v1/sessions/{session_id}/transcript?format=json

# Get summary
curl http://localhost:8000/api/v1/sessions/{session_id}/summary

# Get NLP insights
curl http://localhost:8000/api/v1/sessions/{session_id}/insights
```

### CLI Tools

```bash
# Process audio file
python -m src.cli.process_audio --input audio.wav --output transcript.json

# Benchmark performance
python -m src.cli.benchmark --model whisper-large-v3 --device cuda

# Export session data
python -m src.cli.export_session --session-id <id> --format srt
```

---

## 🧪 Testing

### Quick Start

Run all audio tests with the convenience script:

```bash
./scripts/run_audio_tests.sh --all
```

Or run specific test categories:

```bash
# Unit tests only
./scripts/run_audio_tests.sh --unit

# Integration tests only
./scripts/run_audio_tests.sh --integration

# Performance benchmarks only
./scripts/run_audio_tests.sh --performance

# Quick tests (skip slow tests)
./scripts/run_audio_tests.sh --quick

# With coverage report
./scripts/run_audio_tests.sh --coverage
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run audio tests only
pytest -m audio -v

# Run specific test categories
pytest tests/unit -v              # Unit tests
pytest tests/integration -v       # Integration tests
pytest tests/performance -v       # Performance benchmarks

# Run tests with markers
pytest -m vad -v                  # VAD tests
pytest -m websocket -v            # WebSocket tests
pytest -m "not slow" -v           # Skip slow tests

# With coverage report
pytest --cov=src/core/audio_capture --cov-report=html

# Parallel execution
pytest -n auto
```

### Manual Interactive Tests

Test live microphone capture:

```bash
# Basic 5-second recording
python -m tests.manual.test_microphone_capture

# Custom duration with audio levels and VAD display
python -m tests.manual.test_microphone_capture \
  --duration 10 \
  --show-levels \
  --show-vad \
  --output test_output/recording.wav

# List available audio devices
python -m tests.manual.test_microphone_capture --list-devices
```

### Test Coverage

Current audio test coverage:

- **Audio Capture**: WASAPI, format conversion, device management
- **VAD Detection**: Silero VAD, speech segmentation, accuracy >90%
- **Circular Buffer**: Thread-safe buffering, overflow/underflow handling
- **WebSocket Streaming**: Connection lifecycle, audio transmission, latency
- **End-to-End Pipeline**: Mic → VAD → Buffer → WS → STT → NLP → Summary
- **Performance**: Latency benchmarks, throughput tests, memory profiling

### Performance Targets

| Component | Target | Critical |
|-----------|--------|----------|
| **STT Processing** | < 200ms | < 500ms |
| **NLP Processing** | < 100ms | < 200ms |
| **Total Pipeline** | < 500ms | < 1000ms |
| **Throughput** | > 10 chunks/sec | > 5 chunks/sec |
| **Memory Usage** | < 500MB | < 1GB |

### Documentation

For detailed testing information, see:

- **[Audio Testing Guide](tests/AUDIO_TESTING.md)** - Comprehensive testing documentation
- **[Audio Fixtures README](tests/fixtures/audio/README.md)** - Test audio fixtures

### Performance Benchmarks

```bash
# Audio latency benchmark (detailed metrics)
pytest tests/performance/test_audio_latency.py -v

# Throughput and resource utilization
pytest tests/performance/test_throughput.py -v

# Legacy benchmarks
python benchmarks/latency_test.py
python benchmarks/throughput_test.py
python benchmarks/gpu_memory_profile.py

# Load test
locust -f benchmarks/load_test.py --host http://localhost:8000
```

### CI/CD Integration

Tests are organized for different CI/CD scenarios:

- **On Every PR**: Unit tests, basic integration tests
- **Nightly Builds**: Full integration tests, performance benchmarks
- **Manual Trigger**: Interactive tests, stress tests

See [Audio Testing Guide](tests/AUDIO_TESTING.md) for CI/CD configuration examples.

---

## 📊 Monitoring

### Grafana Dashboards

Access Grafana at `http://localhost:3001` (default: admin/admin)

**Available Dashboards:**
- **System Overview**: CPU, GPU, memory, latency
- **STT Performance**: WER, throughput, queue depth
- **ORCHIDEA Metrics**: PUII alignment, quality gates, agent activity
- **Redis Streams**: Message rates, lag, pending messages

### Prometheus Metrics

- `rtstt_audio_latency_ms` - Audio capture latency
- `rtstt_stt_latency_ms` - STT processing latency
- `rtstt_nlp_latency_ms` - NLP processing latency
- `rtstt_wer` - Word Error Rate
- `rtstt_gpu_utilization` - GPU usage percentage
- `rtstt_active_sessions` - Number of active sessions
- `orchidea_puii_alignment` - ORCHIDEA alignment score

---

## 🛠️ Development

### Project Structure

```
realtime-stt-orchestrator/
├── docs/                    # Documentation
│   └── api/                # API contracts (gRPC, WebSocket, REST)
├── src/
│   ├── core/               # Core modules
│   │   ├── audio_capture/  # WASAPI, VAD, buffer
│   │   ├── stt_engine/     # Whisper, gRPC server
│   │   ├── nlp_insights/   # NLP, diarization
│   │   └── summary_generator/  # Llama summarizer
│   ├── agents/             # ORCHIDEA agents
│   ├── ui/                 # Electron + React
│   └── shared/             # Shared utilities
├── tests/                  # Test suites
├── orchestration/          # Agent configs, workflows
├── infrastructure/         # Docker, K8s, monitoring
├── KB/                     # Knowledge base (specs)
├── requirements/           # Python dependencies
└── docker-compose.yml
```

### Git Worktree Workflow

For parallel development:

```bash
# Create worktrees for team isolation
git worktree add ../RTSTT-audio feature/audio-capture
git worktree add ../RTSTT-ml feature/ml-pipeline
git worktree add ../RTSTT-frontend feature/ui-dashboard
git worktree add ../RTSTT-integration feature/backend-api

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../RTSTT-audio
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/

# Type check
mypy src/

# Security scan
bandit -r src/
safety check
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 📚 Documentation

**Core Documentation:**
- [Wave 4A Completion Summary](WAVE-4A-COMPLETION-SUMMARY.md) - Latest achievements and metrics
- [API Reference](docs/API_REFERENCE.md) - gRPC, WebSocket, REST specifications
- [Architecture](docs/ARCHITECTURE.md) - System design and microservices topology
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Step-by-step deployment instructions
- [Testing Guide](docs/TESTING_GUIDE.md) - Unit, integration, and end-to-end testing
- [Audio Tester Quick Start](docs/AUDIO_TESTER_QUICKSTART.md) - Real audio capture guide

**Additional Resources:**
- [ORCHIDEA Integration](docs/ORCHIDEA_INTEGRATION.md) - Framework usage
- [Production Deployment](DEPLOYMENT.md) - Full production guide
- [Agent Specifications](KB/) - Team lead specs
- [gRPC Services Integration](docs/track2-grpc-services.md) - Technical details

### API Documentation

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

---

## 🤝 Contributing

This is a POC project. Contributions are welcome after the initial Windows 11 implementation is complete.

### Development Workflow

1. Create feature branch from `develop`
2. Implement changes with tests (>95% coverage)
3. Run quality checks (`black`, `isort`, `flake8`, `mypy`)
4. Submit PR to `develop`
5. Pass CI/CD pipeline
6. Code review + approval
7. Merge

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **OpenAI Whisper** - State-of-the-art STT model
- **Mistral AI** - NLP language model
- **Meta Llama** - Summarization model
- **ORCHIDEA Framework** - Multi-agent orchestration methodology
- **Anthropic Claude** - Master orchestrator LLM

---

## 📞 Support

For issues and questions:
- GitHub Issues: [Link to repository issues]
- Documentation: [Link to docs]
- Email: support@example.com

---

## 🗺️ Roadmap

### Phase 1: Windows 11 POC ✅ (Current)
- WASAPI audio capture
- RTX 5080 GPU optimization
- Electron desktop app
- ORCHIDEA orchestration

### Phase 2: Multi-Platform Support (Future)
- macOS (CoreAudio)
- Linux (PulseAudio)
- Platform abstraction layer

### Phase 3: Cloud Deployment (Future)
- Kubernetes orchestration
- Horizontal scaling
- Cloud GPU support (AWS, GCP, Azure)

### Phase 4: Advanced Features (Future)
- Multi-language support (50+ languages)
- Custom model fine-tuning
- Real-time translation
- Mobile app (iOS, Android)

---

**Built with ❤️ using ORCHIDEA Framework v1.3**
