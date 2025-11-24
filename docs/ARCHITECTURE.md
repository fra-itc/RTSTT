# RTSTT System Architecture

**Real-Time Speech-to-Text Orchestrator - Complete System Design**

**Version:** 1.0 (Wave 4A)
**Last Updated:** November 24, 2025

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Service Communication](#service-communication)
4. [Data Flow](#data-flow)
5. [Service Details](#service-details)
6. [Deployment Architecture](#deployment-architecture)
7. [Connection Pooling](#connection-pooling)
8. [Error Handling](#error-handling)
9. [Scalability](#scalability)

---

## System Overview

RTSTT is a **distributed microservices architecture** designed for real-time speech-to-text processing with NLP insights and automatic summarization. The system uses **gRPC** for inter-service communication and **WebSocket** for frontend-backend communication.

### Core Components

1. **Frontend (Electron + React)**
   - Desktop application with real-time UI
   - Web Audio API for microphone capture
   - WebSocket connection to backend

2. **Backend Gateway (FastAPI)**
   - WebSocket endpoint for frontend
   - gRPC client pool for service communication
   - Request orchestration and response aggregation
   - REST API for programmatic access

3. **ML Services (gRPC)**
   - **STT Engine**: Whisper V3 speech-to-text
   - **NLP Service**: Keyword extraction, entity recognition, sentiment
   - **Summary Service**: Llama-3.2 based summarization with caching

4. **Infrastructure**
   - Redis for caching and message queues
   - Prometheus for metrics collection
   - Grafana for visualization
   - Docker Compose for orchestration

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Electron Desktop Application                                    │   │
│  │  ├─ AudioTester Component (Web Audio API)                       │   │
│  │  ├─ Real microphone capture                                     │   │
│  │  ├─ Waveform visualization                                      │   │
│  │  ├─ Transcription display                                       │   │
│  │  ├─ NLP insights display                                        │   │
│  │  └─ Summary display                                             │   │
│  └─────────────────────┬───────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────────────┘
                       │ WebSocket
                       │ ws://localhost:8000/ws
                       ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                      BACKEND GATEWAY LAYER                                │
│                      FastAPI (Port 8000)                                  │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  WebSocket Handler                                               │   │
│  │  ├─ Audio chunk reception                                        │   │
│  │  ├─ Audio buffering (2-second chunks)                            │   │
│  │  ├─ VAD integration                                              │   │
│  │  └─ Response aggregation                                         │   │
│  └──────────────────────┬───────────────────────────────────────────┘   │
│                         │                                                 │
│  ┌──────────┬───────────┼──────────────┬──────────────────────────┐     │
│  │          │           │              │                          │     │
│  ↓          ↓           ↓              ↓                          ↓     │
│
│ ┌─────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│ │ gRPC Client     │ │ gRPC Client      │ │ REST API         │            │
│ │ STT Engine      │ │ NLP Service      │ │ Endpoints        │            │
│ │ (50051)         │ │ (50052)          │ │ /api/v1/*        │            │
│ │                 │ │                  │ │                  │            │
│ │ Connection      │ │ Connection       │ │ Health checks    │            │
│ │ pooling         │ │ pooling          │ │ Metrics endpoint │            │
│ │ Timeout: 30s    │ │ Timeout: 30s     │ │                  │            │
│ └────────┬────────┘ └───────┬──────────┘ └──────────────────┘            │
│          │                  │                                             │
└──────────┼──────────────────┼─────────────────────────────────────────────┘
           │                  │
           │                  └─────────┐
           │                            │ gRPC
           ↓                            ↓
┌────────────────────────┬──────────────────────────────────────────────────┐
│                  ML SERVICES LAYER                                         │
│              Docker Container Network                                      │
│                                                                           │
│  ┌──────────────────────────┐  ┌─────────────────────────────────┐      │
│  │ STT Engine Service       │  │ NLP Service                     │      │
│  │ Port: 50051              │  │ Port: 50052                     │      │
│  │                          │  │                                 │      │
│  │ ├─ Whisper V3            │  │ ├─ Keyword extraction           │      │
│  │ ├─ RTX 5080 GPU          │  │ ├─ Entity recognition (NER)     │      │
│  │ ├─ <250ms latency        │  │ ├─ Sentiment analysis           │      │
│  │ └─ Proto: gRPC health    │  │ ├─ <50ms latency               │      │
│  │                          │  │ └─ Proto: gRPC health          │      │
│  └──────────────────────────┘  └─────────────────────────────────┘      │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │ Summary Service                                              │       │
│  │ Port: 50053                                                  │       │
│  │                                                              │       │
│  │ ├─ Llama-3.2-8B-Instruct                                     │       │
│  │ ├─ RTX 5080 GPU                                              │       │
│  │ ├─ 150-180ms latency (uncached)                              │       │
│  │ ├─ 5-10ms latency (cached)                                   │       │
│  │ ├─ Redis caching (60-80% hit rate)                           │       │
│  │ └─ Proto: gRPC health                                        │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                                                                           │
└───────────┬──────────────────────────────────────────────────────────────┘
            │
            └──────────────────┬─────────────────────────┐
                               ↓                         ↓
                    ┌──────────────────┐    ┌──────────────────┐
                    │  Redis Cache     │    │  Redis Streams   │
                    │  Port: 6379      │    │  Port: 6379      │
                    │                  │    │                  │
                    │ ├─ Summary cache │    │ ├─ Message queue │
                    │ ├─ TTL: 3600s    │    │ ├─ Session logs  │
                    │ └─ Key: SHA256   │    │ └─ Audit trail   │
                    └──────────────────┘    └──────────────────┘
```

---

## Service Communication

### Communication Protocols

#### 1. WebSocket (Frontend ↔ Backend)

**Purpose:** Real-time audio streaming and response delivery

**Message Format:**
```json
{
  "type": "audio_chunk|transcription|insights|summary",
  "timestamp": 1732411200000,
  "session_id": "session_123",
  "payload": {
    "audio_data": "base64_encoded_audio",
    "text": "transcription result",
    "confidence": 0.95,
    "keywords": ["word1", "word2"],
    "summary": "Short summary...",
    "latency_ms": 285
  }
}
```

**Connection Lifecycle:**
1. Client connects to `ws://localhost:8000/ws`
2. Backend accepts and creates session
3. Client sends audio chunks
4. Backend processes and sends results
5. Client disconnects or timeout

**Performance:**
- Latency: <10ms
- Throughput: 2 Mbps (typical for 2-second audio chunks)
- Connection pool size: Unlimited (HTTP connection)

#### 2. gRPC (Backend ↔ Services)

**Purpose:** High-performance inter-service communication

**Protocol Details:**
- Version: gRPC v1
- HTTP/2 multiplexing
- Protocol Buffers 3 serialization
- Bidirectional streaming support

**Services:**

| Service | Port | RPC Methods |
|---------|------|-------------|
| STT | 50051 | Transcribe, HealthCheck |
| NLP | 50052 | ExtractInsights, HealthCheck |
| Summary | 50053 | GenerateSummary, GenerateSummaryBatch, HealthCheck |

**Request Timeout:** 30 seconds (configurable)

**Performance:**
- Latency: <5ms (same Docker network)
- Throughput: 100+ concurrent connections per service
- Serialization overhead: <1ms

#### 3. REST API (External Integration)

**Purpose:** HTTP API for external integrations

**Endpoints:**
- `GET /health` - Overall system health
- `GET /health/services` - Individual service health
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}/transcript` - Get transcript
- `GET /api/v1/sessions/{id}/summary` - Get summary
- `GET /api/v1/sessions/{id}/insights` - Get NLP insights
- `GET /metrics` - Prometheus metrics

---

## Data Flow

### Complete End-to-End Flow

```
Step 1: Audio Capture
├─ Frontend: Web Audio API captures microphone
├─ Data: 2-second audio chunks (16kHz, mono, PCM)
├─ Size: ~64KB per chunk
└─ Frequency: Every 2 seconds

Step 2: WebSocket Transmission
├─ Frontend: Sends audio chunk via WebSocket
├─ Backend: Receives and buffers
├─ Protocol: WebSocket JSON message
└─ Latency: <10ms

Step 3: Backend Processing
├─ Backend: Validates audio chunk
├─ Backend: Initiates gRPC calls (in parallel):
│  ├─ STT Service: Transcribe audio
│  ├─ NLP Service: Extract insights (parallel with response)
│  └─ Summary Service: Summarize (parallel with response)
└─ Pipeline: Async/concurrent execution

Step 4: STT Processing
├─ Service: Whisper V3 model
├─ Input: Audio chunk (WAV format)
├─ Output: Transcription text + confidence
├─ Models: Large V3 (default), Medium, Base, Tiny
└─ Latency: 250-311ms

Step 5: NLP Processing (Parallel)
├─ Service: KeyBERT + SentenceTransformers
├─ Input: Transcription text
├─ Processing:
│  ├─ Keyword extraction (top-10)
│  ├─ Entity recognition (NER)
│  └─ Sentiment analysis
├─ Output: Keywords + entities + sentiment
└─ Latency: 30-40ms

Step 6: Summary Processing (Parallel)
├─ Service: Llama-3.2-8B-Instruct
├─ Input: Transcription text
├─ Processing:
│  ├─ Check Redis cache (key: SHA256(text))
│  ├─ If found: Return cached summary
│  ├─ If not: Generate with Llama model
│  └─ Store in cache (TTL: 3600s)
├─ Output: Summary text + cache hit flag
└─ Latency: 5-10ms (cached) or 150-180ms (uncached)

Step 7: Response Aggregation
├─ Backend: Wait for all services (parallel execution)
├─ Backend: Combine results:
│  ├─ Transcription (from STT)
│  ├─ Confidence (from STT)
│  ├─ Keywords (from NLP)
│  ├─ Sentiment (from NLP)
│  ├─ Summary (from Summary service)
│  └─ Latency metrics
├─ Backend: Measure total latency
└─ Latency: <5ms

Step 8: WebSocket Response
├─ Backend: Send aggregated results
├─ Frontend: Receive and display
├─ UI Updates:
│  ├─ Transcription text
│  ├─ Confidence percentage
│  ├─ Keywords list
│  ├─ Sentiment indicator
│  ├─ Summary text
│  └─ Latency badge
└─ Latency: <5ms

Step 9: Frontend Display
├─ AudioTester: Update transcriptions panel
├─ AudioTester: Update keywords panel
├─ AudioTester: Update summary panel
├─ AudioTester: Update statistics
└─ User sees: Real-time results with metrics
```

### Total Latency Breakdown

| Component | Time | Percentage |
|-----------|------|-----------|
| Audio capture to WebSocket send | <10ms | 3% |
| WebSocket transmission | <5ms | 2% |
| STT processing | 250-311ms | 82-89% |
| NLP processing (parallel) | 30-40ms | - |
| Summary processing (parallel) | 150-180ms | - |
| Response aggregation | <5ms | 2% |
| WebSocket response | <5ms | 2% |
| **Total (with parallelization)** | **253-312ms** | **100%** |

**Key insight:** Total time ≈ STT time (slowest service) + small overhead due to parallelization.

---

## Service Details

### 1. STT Engine Service

**Port:** 50051
**Image:** `nvidia/cuda:12.8.0-runtime-ubuntu22.04` + Whisper V3
**GPU:** RTX 5080 (compute capability 12.0)

**Proto Definition:**
```protobuf
service STTService {
  rpc Transcribe(AudioRequest) returns (TranscriptionResponse);
  rpc HealthCheck(Empty) returns (HealthCheckResponse);
}

message AudioRequest {
  bytes audio_data = 1;      // WAV format
  string language = 2;        // e.g., "en", "it"
  string model = 3;           // "base", "small", "medium", "large-v3"
}

message TranscriptionResponse {
  string text = 1;
  float confidence = 2;       // 0.0 - 1.0
  int32 latency_ms = 3;
}
```

**Configuration:**
```yaml
Environment Variables:
  DEVICE: cuda
  MODEL_SIZE: large-v3
  FP16: true
  GPU_MEMORY_FRACTION: 0.7
```

**Performance:**
- Model: Whisper Large V3
- Latency: 250-311ms (typical)
- Throughput: 10+ concurrent (limited by GPU memory)
- Accuracy: WER < 5%
- Memory: ~11GB GPU, 2GB host

**Health Check:**
- RPC: `HealthCheck(Empty)` returns status
- Interval: 30 seconds (from backend)
- Timeout: 5 seconds
- Failure threshold: 3 consecutive failures → marked unhealthy

### 2. NLP Service

**Port:** 50052
**Image:** `nvidia/cuda:12.8.0-runtime-ubuntu22.04` + KeyBERT/SentenceTransformers
**GPU:** RTX 5080 (compute capability 12.0)

**Proto Definition:**
```protobuf
service NLPService {
  rpc ExtractInsights(TranscriptionRequest) returns (InsightsResponse);
  rpc HealthCheck(Empty) returns (HealthCheckResponse);
}

message TranscriptionRequest {
  string text = 1;
  string session_id = 2;
  int32 top_keywords = 3;
}

message InsightsResponse {
  repeated Keyword keywords = 1;
  repeated Entity entities = 2;
  Sentiment sentiment = 3;
  int32 latency_ms = 4;
}

message Keyword {
  string keyword = 1;
  float score = 2;
}

message Entity {
  string text = 1;
  string type = 2;      // PERSON, ORG, LOCATION, etc.
  float confidence = 3;
}

message Sentiment {
  string polarity = 1;  // POSITIVE, NEGATIVE, NEUTRAL
  float score = 2;      // 0.0 - 1.0
}
```

**Configuration:**
```yaml
Environment Variables:
  DEVICE: cuda
  MODEL_NAME: all-MiniLM-L6-v2
  TOP_KEYWORDS: 10
  NER_MODEL: dbmdz/bert-base-multilingual-uncased
```

**Performance:**
- Latency: 30-40ms typical
- Throughput: 100+ concurrent
- Memory: ~2GB GPU, 1GB host
- Accuracy: Top-10 keywords (precision >90%)

**Features:**
- Keyword extraction (KeyBERT)
- Named entity recognition (spaCy)
- Sentiment analysis (TextBlob/VADER)
- Multi-language support

**Health Check:**
- RPC: `HealthCheck(Empty)` returns status
- Interval: 30 seconds (from backend)
- Timeout: 5 seconds
- Failure threshold: 3 consecutive failures → marked unhealthy

### 3. Summary Service

**Port:** 50053
**Image:** `nvidia/cuda:12.8.0-runtime-ubuntu22.04` + Llama-3.2
**GPU:** RTX 5080 (compute capability 12.0)
**Cache:** Redis (port 6379)

**Proto Definition:**
```protobuf
service SummaryService {
  rpc GenerateSummary(TextRequest) returns (SummaryResponse);
  rpc GenerateSummaryBatch(BatchTextRequest) returns (BatchSummaryResponse);
  rpc HealthCheck(Empty) returns (HealthCheckResponse);
}

message TextRequest {
  string text = 1;
  string session_id = 2;
  int32 max_length = 3;     // Default: 100
  float temperature = 4;    // Default: 0.7
}

message SummaryResponse {
  string summary = 1;
  bool cache_hit = 2;
  int32 latency_ms = 3;
  string cache_key = 4;     // For debugging
}

message BatchTextRequest {
  repeated TextRequest requests = 1;
}

message BatchSummaryResponse {
  repeated SummaryResponse responses = 1;
}
```

**Cache Strategy:**
```
Key Format: summary_cache:v1:{sha256(text)[:16]}
TTL: 3600 seconds (1 hour)
Max Size: Redis memory limit
Eviction: LRU when full

Hit Rate: 60-80% typical
Cache Layer: Redis (port 6379)
```

**Configuration:**
```yaml
Environment Variables:
  DEVICE: cuda
  MODEL_NAME: meta-llama/Llama-3.2-8B-Instruct
  MAX_LENGTH: 100
  TEMPERATURE: 0.7
  QUANTIZATION: true
  REDIS_HOST: redis
  REDIS_PORT: 6379
  CACHE_TTL: 3600
```

**Performance:**
- Latency (uncached): 150-180ms
- Latency (cached): 5-10ms
- Throughput: 50+ concurrent
- Memory: ~4GB GPU, 1GB host
- Cache hit rate: 60-80% typical

**Features:**
- Llama-3.2-8B-Instruct summarization
- Temperature control for output variability
- Batch processing support (up to 32)
- Automatic cache invalidation
- Summary length control

**Health Check:**
- RPC: `HealthCheck(Empty)` returns status
- Interval: 30 seconds (from backend)
- Timeout: 5 seconds
- Failure threshold: 3 consecutive failures → marked unhealthy

---

## Deployment Architecture

### Docker Compose Structure

```yaml
version: '3.8'

services:
  # Infrastructure
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Monitoring
  prometheus:
    image: prom/prometheus:v2.50.0
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3001:3000"

  # ML Services
  stt-engine:
    image: rtstt/stt-engine:latest
    ports:
      - "50051:50051"
    gpu: all
    environment:
      - DEVICE=cuda

  nlp-service:
    image: rtstt/nlp-service:latest
    ports:
      - "50052:50052"
    gpu: all
    environment:
      - DEVICE=cuda

  summary-service:
    image: rtstt/summary-service:latest
    ports:
      - "50053:50053"
    gpu: all
    environment:
      - DEVICE=cuda
      - REDIS_HOST=redis

  # Backend Gateway
  backend:
    image: rtstt/backend:latest
    ports:
      - "8000:8000"
    depends_on:
      - stt-engine
      - nlp-service
      - summary-service
      - redis
    environment:
      - STT_SERVICE_HOST=stt-engine
      - NLP_SERVICE_HOST=nlp-service
      - SUMMARY_SERVICE_HOST=summary-service
      - REDIS_HOST=redis
```

### Network Topology

```
┌─────────────────────────────────────────────────────┐
│          Docker Network (rtstt-network)              │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ STT Engine  │  │ NLP Service  │  │ Summary  │  │
│  │ :50051      │  │ :50052       │  │ :50053   │  │
│  └──────┬──────┘  └───────┬──────┘  └────┬─────┘  │
│         │                 │              │        │
│         └─────────────────┼──────────────┘        │
│                           │                       │
│                    ┌──────┴──────┐                │
│                    │   Backend   │                │
│                    │   :8000     │                │
│                    └──────┬──────┘                │
│                           │                       │
│                    ┌──────▼──────┐                │
│                    │    Redis    │                │
│                    │   :6379     │                │
│                    └─────────────┘                │
│                                                     │
└─────────────────────────────────────────────────────┘
        ↑
        │ HTTP/WebSocket
        │
    Browser/Desktop Client
```

### Port Mapping

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Backend | 8000 | HTTP/WS | Frontend communication |
| Prometheus | 9090 | HTTP | Metrics scraping |
| Grafana | 3001 | HTTP | Visualization |
| STT Engine | 50051 | gRPC | Speech-to-text |
| NLP Service | 50052 | gRPC | NLP insights |
| Summary Service | 50053 | gRPC | Text summarization |
| Redis | 6379 | Redis | Caching & queues |

---

## Connection Pooling

### Backend → gRPC Services

**Implementation:** gRPC channel pooling with round-robin load balancing

```python
class GRPCConnectionPool:
    def __init__(self, host: str, port: int, pool_size: int = 5):
        self.channels = [
            grpc.secure_channel(f"{host}:{port}")
            for _ in range(pool_size)
        ]
        self.current_index = 0

    def get_channel(self) -> grpc.Channel:
        """Round-robin channel selection"""
        channel = self.channels[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.channels)
        return channel
```

**Configuration:**
```python
# Connection pool sizes
NLP_POOL_SIZE = 10
SUMMARY_POOL_SIZE = 10
STT_POOL_SIZE = 5

# Timeouts
GRPC_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 30  # seconds
```

**Benefits:**
- Load distribution across connections
- Connection reuse (HTTP/2 multiplexing)
- Timeout handling per connection
- Automatic failover on connection failure

### Frontend → Backend

**Implementation:** Single WebSocket connection per session

```javascript
class WebSocketManager {
    constructor(url) {
        this.ws = new WebSocket(url);
        this.messageQueue = [];
        this.sessionId = generateUUID();
    }

    send(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }
}
```

**Connection Lifecycle:**
1. Frontend initiates WebSocket to backend
2. Backend accepts and creates session
3. Frontend sends audio chunks
4. Backend processes and sends responses
5. On disconnect: Clean up session resources

---

## Error Handling

### Service-Level Error Handling

**gRPC Status Codes:**
```
OK (0): Success
INVALID_ARGUMENT (3): Bad input (e.g., empty text)
DEADLINE_EXCEEDED (4): Timeout (service too slow)
NOT_FOUND (5): Resource not found
INTERNAL (13): Internal server error
UNAVAILABLE (14): Service unavailable
```

**Backend Error Handling:**
```python
try:
    response = stub.GenerateSummary(request, timeout=30)
except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        # Timeout - fallback to cached or empty
        return {"summary": "", "error": "Summary generation timeout"}
    elif e.code() == grpc.StatusCode.UNAVAILABLE:
        # Service down - mark unhealthy, continue with STT only
        return {"summary": "", "error": "Summary service unavailable"}
    else:
        # Other error
        return {"summary": "", "error": str(e)}
```

### Connection Failure Handling

**Detection:** Health checks every 30 seconds
**Action on Failure:**
1. Mark service as unhealthy
2. Log error for monitoring
3. Return "service unavailable" to client
4. Retry with exponential backoff
5. Attempt recovery every 30 seconds

### Client Error Handling

**WebSocket Errors:**
```javascript
ws.addEventListener('error', (event) => {
    console.error('WebSocket error:', event);
    updateConnectionStatus('Error');
    // Attempt reconnection after 3 seconds
    setTimeout(reconnect, 3000);
});

ws.addEventListener('close', (event) => {
    console.log('WebSocket closed:', event.code);
    updateConnectionStatus('Disconnected');
    // Handle cleanup
});
```

---

## Scalability

### Horizontal Scaling Strategy

#### Current (Docker Compose)
- Single instance of each service
- Manual scaling via manual replica management
- No auto-scaling

#### Recommended (Kubernetes)
- Multiple replicas per service
- Auto-scaling based on CPU/memory
- Service mesh for load balancing
- Rolling updates for zero downtime

### Scaling Limitations

**Frontend:**
- Single Electron application per user
- Scales via multiple desktop instances

**Backend Gateway:**
- Single instance per deployment
- Scales via load balancer + multiple replicas
- Stateless design enables horizontal scaling

**STT Engine:**
- GPU-bound (RTX 5080 capacity)
- 10+ concurrent requests max per GPU
- Scale via multiple GPUs or multiple instances

**NLP Service:**
- CPU-optimized (can run on CPU or GPU)
- 100+ concurrent requests
- Easy to replicate

**Summary Service:**
- GPU-bound for generation, CPU for caching
- Cache hit rate improves with more instances
- 50+ concurrent requests per instance
- Easy to replicate

### Load Testing Targets

| Service | Current | Target | Method |
|---------|---------|--------|--------|
| Backend | 10 req/s | 50+ req/s | Reverse proxy load balancer |
| STT | 10 concurrent | 50+ concurrent | Multiple GPUs + routing |
| NLP | 100 concurrent | 500+ concurrent | Multiple instances + LB |
| Summary | 50 concurrent | 200+ concurrent | Multiple instances + LB |

### Recommended Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nlp-service
spec:
  replicas: 3  # Start with 3
  selector:
    matchLabels:
      app: nlp-service
  template:
    metadata:
      labels:
        app: nlp-service
    spec:
      containers:
      - name: nlp-service
        image: rtstt/nlp-service:latest
        ports:
        - containerPort: 50052
        resources:
          requests:
            cpu: "2"
            memory: "2Gi"
          limits:
            cpu: "4"
            memory: "4Gi"
        livenessProbe:
          grpc:
            port: 50052
          initialDelaySeconds: 30
          periodSeconds: 30
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nlp-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nlp-service
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring & Observability

### Prometheus Metrics

**Service Metrics:**
```
rtstt_stt_latency_ms (histogram)
rtstt_nlp_latency_ms (histogram)
rtstt_summary_latency_ms (histogram)
rtstt_summary_cache_hits (counter)
rtstt_summary_cache_misses (counter)
rtstt_active_sessions (gauge)
rtstt_gpu_memory_used_percent (gauge)
rtstt_gpu_utilization_percent (gauge)
```

**Access:** http://localhost:9090

### Grafana Dashboards

**Available Dashboards:**
1. System Overview: CPU, GPU, memory, network
2. STT Performance: Latency, throughput, WER
3. NLP Performance: Latency, keyword accuracy
4. Summary Performance: Latency, cache hit rate
5. Service Health: Status of all services

**Access:** http://localhost:3001

---

## Security Considerations

### Current State (Wave 4A)
- gRPC communication unencrypted (HTTP/2 plaintext)
- No service-to-service authentication
- No API key authentication for REST API
- No rate limiting

### Recommended Improvements (Future Waves)
1. **TLS/mTLS:** Encrypt gRPC traffic
2. **Service Authentication:** Mutual TLS certificates
3. **API Authentication:** JWT tokens or API keys
4. **Rate Limiting:** Per-client request limits
5. **Network Policies:** Kubernetes network segmentation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-24 | Initial documentation (Wave 4A) |
| - | Future | Kubernetes architecture |
| - | Future | TLS/mTLS implementation |

---

**For deployment instructions, see:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**For API details, see:** [API_REFERENCE.md](API_REFERENCE.md)
**For testing procedures, see:** [TESTING_GUIDE.md](TESTING_GUIDE.md)
