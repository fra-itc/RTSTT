# RTSTT Testing Guide (Wave 4A)

**Comprehensive testing procedures for unit, integration, and end-to-end testing**

**Version:** 1.0
**Last Updated:** November 24, 2025

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Performance Testing](#performance-testing)
6. [Audio Testing](#audio-testing)
7. [gRPC Service Testing](#grpc-service-testing)
8. [Test Infrastructure](#test-infrastructure)
9. [CI/CD Integration](#cicd-integration)

---

## Testing Overview

### Testing Pyramid

```
        ╱╲
       ╱  ╲  E2E Tests
      ╱────╲ (< 10)
     ╱  ╱╲  ╲
    ╱  ╱  ╲  ╲ Integration Tests
   ╱  ╱────╲  ╲ (10-30)
  ╱  ╱  ╱╲  ╲  ╲
 ╱  ╱  ╱  ╲  ╲  ╲ Unit Tests
╱──╱──╱────╲──╲──╲ (100+)
```

### Test Categories

| Level | Count | Execution | Coverage |
|-------|-------|-----------|----------|
| **Unit** | 100+ | <5 sec | 90%+ |
| **Integration** | 30+ | <30 sec | 70%+ |
| **End-to-End** | 10+ | <60 sec | 50%+ |
| **Performance** | 5+ | <120 sec | Key metrics |

### Target Metrics

- **Coverage:** >95% for critical paths
- **Speed:** Full test suite <2 minutes
- **Reliability:** 0 flaky tests
- **Clarity:** Each test has single responsibility

---

## Unit Testing

### Running Unit Tests

**Run all unit tests:**
```bash
pytest tests/unit -v
```

**Run specific module:**
```bash
pytest tests/unit/test_audio_capture.py -v
```

**Run with coverage:**
```bash
pytest tests/unit --cov=src/core --cov-report=html
```

**Run specific test:**
```bash
pytest tests/unit/test_audio_capture.py::test_audio_chunk_creation -v
```

### Unit Test Modules

#### 1. Audio Capture Tests

**File:** `tests/unit/test_audio_capture.py`

**Tests:**
```python
def test_audio_device_enumeration():
    """Verify audio devices are enumerated correctly"""
    devices = AudioManager.enumerate_devices()
    assert len(devices) > 0
    assert all('name' in d for d in devices)

def test_audio_chunk_creation():
    """Verify audio chunks are created with correct format"""
    chunk = AudioChunk(
        data=b'\x00\x00' * 1000,
        sample_rate=16000,
        channels=1,
        format='PCM_16'
    )
    assert chunk.duration_ms == 62.5
    assert len(chunk.data) == 2000

def test_audio_level_calculation():
    """Verify audio level RMS calculation"""
    # Silent audio
    silent_data = b'\x00\x00' * 1000
    silent_level = calculate_rms(silent_data)
    assert silent_level < 10

    # Loud audio
    loud_data = b'\xff\x7f' * 1000  # Max amplitude
    loud_level = calculate_rms(loud_data)
    assert loud_level > 90
```

**Run:**
```bash
pytest tests/unit/test_audio_capture.py -v
```

#### 2. VAD (Voice Activity Detection) Tests

**File:** `tests/unit/test_vad.py`

**Tests:**
```python
def test_vad_silence_detection():
    """Verify VAD detects silence correctly"""
    vad = SileroVAD(threshold=0.5)

    # Silent audio
    silent_audio = np.zeros(16000)  # 1 second silence
    is_speech = vad.predict(silent_audio)
    assert not is_speech

def test_vad_speech_detection():
    """Verify VAD detects speech correctly"""
    vad = SileroVAD(threshold=0.5)

    # Load real speech sample
    speech_audio = load_test_audio('samples/speech.wav')
    is_speech = vad.predict(speech_audio)
    assert is_speech

def test_vad_mixed_audio():
    """Verify VAD handles mixed audio (speech + noise)"""
    vad = SileroVAD(threshold=0.5)

    # Speech + background noise
    mixed_audio = load_test_audio('samples/speech_with_noise.wav')
    is_speech = vad.predict(mixed_audio)
    assert is_speech  # Should still detect speech
```

**Run:**
```bash
pytest tests/unit/test_vad.py -v
```

#### 3. Buffer Tests

**File:** `tests/unit/test_circular_buffer.py`

**Tests:**
```python
def test_buffer_write_and_read():
    """Verify buffer write and read operations"""
    buffer = CircularBuffer(size=1000)

    data = b'test_data' * 100
    buffer.write(data)

    read_data = buffer.read(len(data))
    assert read_data == data

def test_buffer_overflow():
    """Verify buffer handles overflow correctly"""
    buffer = CircularBuffer(size=100)

    large_data = b'x' * 200  # Larger than buffer
    buffer.write(large_data)  # Should not crash

    # Should still be able to read
    read_data = buffer.read(100)
    assert len(read_data) == 100

def test_buffer_thread_safety():
    """Verify buffer is thread-safe"""
    buffer = CircularBuffer(size=1000)

    def writer():
        for i in range(100):
            buffer.write(f'chunk_{i}'.encode())

    def reader():
        for i in range(100):
            buffer.read(100)

    # Run in parallel
    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert buffer.read(100) is not None  # Still works
```

**Run:**
```bash
pytest tests/unit/test_circular_buffer.py -v
```

#### 4. Protocol Buffer Tests

**File:** `tests/unit/test_proto_serialization.py`

**Tests:**
```python
def test_nlp_service_proto_serialization():
    """Verify NLP service proto serialization"""
    from src.core.nlp_insights import nlp_service_pb2

    request = nlp_service_pb2.TranscriptionRequest(
        text="Test text",
        session_id="session_001",
        top_keywords=10
    )

    # Serialize
    serialized = request.SerializeToString()
    assert isinstance(serialized, bytes)

    # Deserialize
    deserialized = nlp_service_pb2.TranscriptionRequest()
    deserialized.ParseFromString(serialized)
    assert deserialized.text == "Test text"

def test_summary_service_proto_batch():
    """Verify Summary service batch proto"""
    from src.core.summary_generator import summary_service_pb2

    batch = summary_service_pb2.BatchTextRequest(
        requests=[
            summary_service_pb2.TextRequest(text=f"Text {i}")
            for i in range(5)
        ]
    )

    assert len(batch.requests) == 5

    # Serialize and deserialize
    serialized = batch.SerializeToString()
    deserialized = summary_service_pb2.BatchTextRequest()
    deserialized.ParseFromString(serialized)
    assert len(deserialized.requests) == 5
```

**Run:**
```bash
pytest tests/unit/test_proto_serialization.py -v
```

---

## Integration Testing

### Running Integration Tests

**Run all integration tests:**
```bash
pytest tests/integration -v
```

**Run specific module:**
```bash
pytest tests/integration/test_grpc_services_integration.py -v
```

**Requires:**
- Redis running (`docker-compose up -d redis`)
- STT Engine running (`docker-compose up -d stt-engine`)
- NLP Service running (`docker-compose up -d nlp-service`)
- Summary Service running (`docker-compose up -d summary-service`)

### Integration Test Modules

#### 1. gRPC Services Integration

**File:** `tests/integration/test_grpc_services_integration.py`

**Tests:**
```python
@pytest.fixture(scope="session")
def grpc_services():
    """Start gRPC services for testing"""
    # Connect to services
    stt_channel = grpc.insecure_channel('localhost:50051')
    nlp_channel = grpc.insecure_channel('localhost:50052')
    summary_channel = grpc.insecure_channel('localhost:50053')

    yield {
        'stt': stt_channel,
        'nlp': nlp_channel,
        'summary': summary_channel
    }

    # Cleanup
    stt_channel.close()
    nlp_channel.close()
    summary_channel.close()

def test_nlp_service_health(grpc_services):
    """Test NLP service health check"""
    from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc

    stub = nlp_service_pb2_grpc.NLPServiceStub(grpc_services['nlp'])
    response = stub.HealthCheck(nlp_service_pb2.Empty())

    assert response.status == 'SERVING'

def test_nlp_extract_insights(grpc_services):
    """Test NLP insight extraction"""
    from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc

    stub = nlp_service_pb2_grpc.NLPServiceStub(grpc_services['nlp'])

    request = nlp_service_pb2.TranscriptionRequest(
        text="The quick brown fox jumps over the lazy dog",
        session_id="test_001",
        top_keywords=5
    )

    response = stub.ExtractInsights(request)

    assert len(response.keywords) > 0
    assert all(0 <= kw.score <= 1 for kw in response.keywords)
    assert response.latency_ms < 50  # Performance target

def test_summary_service_health(grpc_services):
    """Test Summary service health check"""
    from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

    stub = summary_service_pb2_grpc.SummaryServiceStub(grpc_services['summary'])
    response = stub.HealthCheck(summary_service_pb2.Empty())

    assert response.status == 'SERVING'

def test_summary_generation(grpc_services):
    """Test Summary generation"""
    from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

    stub = summary_service_pb2_grpc.SummaryServiceStub(grpc_services['summary'])

    text = "This is a test document. " * 50  # ~300 words
    request = summary_service_pb2.TextRequest(
        text=text,
        session_id="test_001",
        max_length=50
    )

    response = stub.GenerateSummary(request)

    assert len(response.summary) > 0
    assert response.latency_ms < 200  # Performance target

def test_summary_caching(grpc_services):
    """Test Summary caching"""
    from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

    stub = summary_service_pb2_grpc.SummaryServiceStub(grpc_services['summary'])
    text = "Test caching with this text."

    # First request (cache miss)
    request1 = summary_service_pb2.TextRequest(text=text, session_id="test_001")
    response1 = stub.GenerateSummary(request1)
    assert not response1.cache_hit
    latency1 = response1.latency_ms

    # Second request (cache hit)
    request2 = summary_service_pb2.TextRequest(text=text, session_id="test_002")
    response2 = stub.GenerateSummary(request2)
    assert response2.cache_hit  # Should be from cache
    latency2 = response2.latency_ms

    assert latency2 < latency1  # Cached response faster

def test_end_to_end_pipeline(grpc_services):
    """Test complete pipeline: NLP + Summary"""
    from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc
    from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

    import time

    text = "The quick brown fox jumps over the lazy dog. " * 20

    # NLP insights
    nlp_stub = nlp_service_pb2_grpc.NLPServiceStub(grpc_services['nlp'])
    nlp_request = nlp_service_pb2.TranscriptionRequest(
        text=text,
        session_id="e2e_001",
        top_keywords=10
    )

    # Summary
    summary_stub = summary_service_pb2_grpc.SummaryServiceStub(grpc_services['summary'])
    summary_request = summary_service_pb2.TextRequest(
        text=text,
        session_id="e2e_001"
    )

    start_time = time.time()

    nlp_response = nlp_stub.ExtractInsights(nlp_request)
    summary_response = summary_stub.GenerateSummary(summary_request)

    total_latency = (time.time() - start_time) * 1000

    assert nlp_response.latency_ms < 50
    assert summary_response.latency_ms < 200
    assert total_latency < 500  # Total target
```

**Run:**
```bash
# Start services first
docker-compose up -d stt-engine nlp-service summary-service redis

# Run tests
pytest tests/integration/test_grpc_services_integration.py -v
```

#### 2. WebSocket Integration

**File:** `tests/integration/test_websocket_integration.py`

**Tests:**
```python
@pytest.fixture
def websocket_client():
    """Create WebSocket client for testing"""
    client = WebSocketTestClient('ws://localhost:8000/ws')
    client.connect()
    yield client
    client.close()

def test_websocket_connection(websocket_client):
    """Test WebSocket connection establishment"""
    assert websocket_client.is_connected()

def test_websocket_session_start(websocket_client):
    """Test session start message"""
    websocket_client.send({
        'type': 'session_start',
        'timestamp': time.time_ns(),
        'payload': {
            'language': 'en-US',
            'enable_nlp': True,
            'enable_summary': True
        }
    })

    response = websocket_client.receive(timeout=5)
    assert response['type'] == 'session_started'
    assert 'session_id' in response

def test_websocket_audio_transmission(websocket_client):
    """Test audio chunk transmission"""
    # Start session first
    websocket_client.send({
        'type': 'session_start',
        'timestamp': time.time_ns(),
        'payload': {'language': 'en-US'}
    })

    session_response = websocket_client.receive(timeout=5)
    session_id = session_response['session_id']

    # Send audio chunk
    audio_data = load_test_audio('samples/test_audio.wav')
    websocket_client.send({
        'type': 'audio_chunk',
        'timestamp': time.time_ns(),
        'session_id': session_id,
        'payload': {
            'audio_data': base64.b64encode(audio_data).decode(),
            'sample_rate': 16000,
            'channels': 1
        }
    })

    # Receive transcription
    response = websocket_client.receive(timeout=10)
    assert response['type'] == 'transcription'
    assert 'text' in response['payload']
```

**Run:**
```bash
# Start backend
docker-compose up -d backend

# Run tests
pytest tests/integration/test_websocket_integration.py -v
```

---

## End-to-End Testing

### Running E2E Tests

**Run all E2E tests:**
```bash
pytest tests/e2e -v
```

**Run complete system test:**
```bash
pytest tests/e2e/test_complete_pipeline.py -v
```

**Requires:**
- All services running (`docker-compose up -d`)

### E2E Test Modules

#### 1. Complete Pipeline Test

**File:** `tests/e2e/test_complete_pipeline.py`

**Test:**
```python
def test_complete_audio_to_summary_pipeline():
    """Test complete pipeline from audio to summary"""
    import time
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    # Load test audio
    test_audio = load_test_audio('samples/italian_speech.wav')

    # Connect via WebSocket
    ws = WebSocket('ws://localhost:8000/ws')
    ws.connect()

    # Start session
    ws.send({
        'type': 'session_start',
        'timestamp': time.time_ns(),
        'payload': {
            'language': 'it-IT',
            'enable_nlp': True,
            'enable_summary': True
        }
    })

    session_response = ws.receive(timeout=5)
    session_id = session_response['session_id']

    # Send audio in chunks
    chunk_size = 8000  # 0.5 seconds
    for i in range(0, len(test_audio), chunk_size):
        chunk = test_audio[i:i+chunk_size]
        ws.send({
            'type': 'audio_chunk',
            'timestamp': time.time_ns(),
            'session_id': session_id,
            'payload': {
                'audio_data': base64.b64encode(chunk).decode(),
                'sample_rate': 16000,
                'channels': 1,
                'format': 'PCM_16',
                'sequence': i // chunk_size
            }
        })

    # Collect results
    transcriptions = []
    insights = []
    summary = None

    start_time = time.time()
    while time.time() - start_time < 30:  # Max 30 seconds
        try:
            response = ws.receive(timeout=1)

            if response['type'] == 'transcription':
                transcriptions.append(response['payload']['text'])
            elif response['type'] == 'nlp_insights':
                insights.append(response['payload'])
            elif response['type'] == 'summary':
                summary = response['payload']['summary']
        except TimeoutError:
            break

    # Verify results
    assert len(transcriptions) > 0, "No transcriptions received"
    assert len(insights) > 0, "No insights received"
    assert summary is not None, "No summary received"

    # Verify content
    full_transcription = ' '.join(transcriptions)
    assert len(full_transcription) > 10, "Transcription too short"
    assert len(summary) > 5, "Summary too short"

    # Verify performance
    pipeline_latency = time.time() - start_time
    assert pipeline_latency < 30, "Pipeline took too long"

    ws.close()
```

---

## Performance Testing

### Load Testing

**Run performance tests:**
```bash
pytest tests/performance -v -m performance
```

### Latency Benchmarking

**File:** `tests/performance/test_latency_benchmarks.py`

**Test:**
```python
def test_stt_latency(benchmark):
    """Benchmark STT latency"""
    import grpc
    from src.core.stt_engine import stt_service_pb2, stt_service_pb2_grpc

    # Load test audio
    audio_data = load_test_audio('samples/test_audio.wav')

    def measure():
        channel = grpc.insecure_channel('localhost:50051')
        stub = stt_service_pb2_grpc.STTServiceStub(channel)

        request = stt_service_pb2.AudioRequest(
            audio_data=audio_data,
            language='en'
        )

        response = stub.Transcribe(request)
        channel.close()
        return response.latency_ms

    result = benchmark(measure)
    assert result < 400, f"STT latency {result}ms exceeds target"

def test_nlp_latency(benchmark):
    """Benchmark NLP latency"""
    text = "The quick brown fox jumps over the lazy dog."

    def measure():
        from src.core.nlp_insights import nlp_service
        service = nlp_service.NLPService()
        response = service.extract_insights(text)
        return response['latency_ms']

    result = benchmark(measure)
    assert result < 50, f"NLP latency {result}ms exceeds target"

def test_summary_latency_uncached(benchmark):
    """Benchmark Summary latency (uncached)"""
    text = "This is a test " * 50

    # Clear cache first
    from src.backend.cache import clear_cache
    clear_cache()

    def measure():
        from src.core.summary_generator import summary_service
        service = summary_service.SummaryService()
        response = service.generate_summary(text)
        return response['latency_ms']

    result = benchmark(measure)
    assert result < 250, f"Summary latency {result}ms exceeds target"

def test_summary_latency_cached(benchmark):
    """Benchmark Summary latency (cached)"""
    text = "This is a cached " * 50

    # Prime cache
    from src.core.summary_generator import summary_service
    service = summary_service.SummaryService()
    service.generate_summary(text)

    def measure():
        response = service.generate_summary(text)
        return response['latency_ms']

    result = benchmark(measure)
    assert result < 20, f"Cached summary latency {result}ms exceeds target"
```

**Run:**
```bash
pytest tests/performance/test_latency_benchmarks.py -v --benchmark-only
```

### Throughput Testing

```bash
# Generate load with 50 concurrent requests
locust -f tests/performance/load_test.py --host http://localhost:8000 --users 50 --spawn-rate 5 -t 10m
```

---

## Audio Testing

### Using AudioTester Component

**File:** `src/ui/components/AudioTester.tsx`

**Manual Test Procedure:**

1. **Start Frontend:**
```bash
cd src/ui
npm run dev
```

2. **Select Microphone:**
   - Open AudioTester
   - Click microphone dropdown
   - Select device

3. **Record Test:**
   - Click "Start Test"
   - Speak for 10-30 seconds
   - Click "Stop"

4. **Verify Results:**
   - Check transcription accuracy
   - Verify confidence scores (should be >0.7)
   - Check latency (<500ms)

5. **Download Logs:**
   - Click save icon
   - Open JSON file
   - Verify all metrics present

### Automated Audio Testing

**File:** `tests/test_audio_testing_suite.py`

**Run:**
```bash
pytest tests/test_audio_testing_suite.py -v
```

---

## gRPC Service Testing

### Using grpcurl

**Install grpcurl:**
```bash
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
```

**Test NLP Service:**
```bash
# List service methods
grpcurl -plaintext localhost:50052 list

# Call ExtractInsights
grpcurl -plaintext \
  -d '{"text":"Hello world","session_id":"test1","top_keywords":5}' \
  localhost:50052 nlp_service.NLPService/ExtractInsights

# Check health
grpcurl -plaintext localhost:50052 grpc.health.v1.Health/Check
```

**Test Summary Service:**
```bash
grpcurl -plaintext \
  -d '{"text":"This is a test...","session_id":"test1"}' \
  localhost:50053 summary_service.SummaryService/GenerateSummary
```

### Python gRPC Testing

```python
import grpc
from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc

# Connect
channel = grpc.secure_channel('localhost:50052', grpc.ssl_channel_credentials())
stub = nlp_service_pb2_grpc.NLPServiceStub(channel)

# Test with timeout
try:
    response = stub.ExtractInsights(
        nlp_service_pb2.TranscriptionRequest(
            text="Test",
            session_id="test1"
        ),
        timeout=10
    )
    print("Success:", response)
except grpc.RpcError as e:
    print(f"Error: {e.code()}: {e.details()}")
finally:
    channel.close()
```

---

## Test Infrastructure

### Test Fixtures

**File:** `tests/conftest.py`

```python
import pytest
import docker
from docker.types import Mount

@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()

@pytest.fixture(scope="session")
def redis_container(docker_client):
    """Start Redis container for testing"""
    container = docker_client.containers.run(
        'redis:7.2-alpine',
        ports={'6379/tcp': 6379},
        detach=True,
        remove=True
    )
    yield container
    container.stop()

@pytest.fixture(scope="session")
def test_audio_files():
    """Load test audio files"""
    return {
        'silence': load_audio('tests/fixtures/silence.wav'),
        'speech': load_audio('tests/fixtures/speech.wav'),
        'noise': load_audio('tests/fixtures/noise.wav'),
        'mixed': load_audio('tests/fixtures/mixed.wav')
    }

@pytest.fixture
def grpc_channel():
    """Create gRPC channel for testing"""
    channel = grpc.insecure_channel('localhost:50052')
    yield channel
    channel.close()
```

### Test Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
addopts = -v --tb=short
timeout = 300
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/tests.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7.2-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements/test.txt

      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Test Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E test passes
- [ ] Performance targets met (<500ms total)
- [ ] Code coverage >95% for critical paths
- [ ] No flaky tests (consistent results)
- [ ] WebSocket connection stable
- [ ] gRPC services responsive
- [ ] Audio quality acceptable
- [ ] Latency within targets

---

**For API details, see:** [API_REFERENCE.md](API_REFERENCE.md)
**For deployment procedures, see:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**For architecture details, see:** [ARCHITECTURE.md](ARCHITECTURE.md)
