# RTSTT API Reference (Wave 4A)

**Complete API documentation for WebSocket, REST, and gRPC interfaces**

**Version:** 1.0
**Last Updated:** November 24, 2025

---

## Table of Contents

1. [WebSocket API](#websocket-api)
2. [REST API](#rest-api)
3. [gRPC API - NLP Service](#grpc-api---nlp-service)
4. [gRPC API - Summary Service](#grpc-api---summary-service)
5. [gRPC API - STT Service](#grpc-api---stt-service)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)

---

## WebSocket API

### Overview

The WebSocket API provides real-time, bidirectional communication for audio streaming and result delivery.

**Endpoint:** `ws://localhost:8000/ws`

**Protocol:** JSON messages over WebSocket
**Connection:** Single persistent connection per session
**Authentication:** None (add JWT in production)

### Message Format

All WebSocket messages follow this structure:

```json
{
  "type": "message_type",
  "timestamp": 1732411200000,
  "session_id": "unique_session_id",
  "payload": {
    "data": "message_specific_payload"
  }
}
```

### Message Types

#### 1. Connection Establishment

**Client → Server: Session Start**
```json
{
  "type": "session_start",
  "timestamp": 1732411200000,
  "payload": {
    "language": "en-US",
    "device_id": "microphone_1",
    "enable_nlp": true,
    "enable_summary": true,
    "enable_vad": true,
    "vad_threshold": 0.3
  }
}
```

**Server → Client: Session Started**
```json
{
  "type": "session_started",
  "timestamp": 1732411200001,
  "session_id": "sess_abc123def456",
  "payload": {
    "status": "connected",
    "server_version": "1.0.0",
    "max_audio_chunk_size": 65536
  }
}
```

#### 2. Audio Streaming

**Client → Server: Audio Chunk**
```json
{
  "type": "audio_chunk",
  "timestamp": 1732411200100,
  "session_id": "sess_abc123def456",
  "payload": {
    "audio_data": "base64_encoded_pcm_audio",
    "sample_rate": 16000,
    "channels": 1,
    "format": "PCM_16",
    "sequence": 1
  }
}
```

**Supported Audio Formats:**
- PCM 16-bit mono
- Sample rate: 8000Hz, 16000Hz, 44100Hz, 48000Hz
- Encoding: base64 in JSON

#### 3. Transcription Results

**Server → Client: Transcription**
```json
{
  "type": "transcription",
  "timestamp": 1732411200200,
  "session_id": "sess_abc123def456",
  "payload": {
    "text": "Hello, this is a test",
    "confidence": 0.92,
    "language": "en",
    "is_final": true,
    "latency_ms": 285,
    "word_count": 5,
    "tokens": {
      "used": 45,
      "limit": 1000
    }
  }
}
```

**Fields:**
- `text` (string): Transcribed text
- `confidence` (float): 0.0-1.0, confidence score
- `language` (string): Detected language code
- `is_final` (boolean): Whether transcription is final or partial
- `latency_ms` (int): Processing time in milliseconds
- `word_count` (int): Number of words in transcription
- `tokens` (object): Token usage information

#### 4. NLP Insights

**Server → Client: NLP Insights**
```json
{
  "type": "nlp_insights",
  "timestamp": 1732411200300,
  "session_id": "sess_abc123def456",
  "payload": {
    "keywords": [
      {
        "keyword": "test",
        "score": 0.95
      },
      {
        "keyword": "hello",
        "score": 0.87
      }
    ],
    "entities": [
      {
        "text": "John",
        "type": "PERSON",
        "confidence": 0.92
      }
    ],
    "sentiment": {
      "polarity": "POSITIVE",
      "score": 0.75
    },
    "latency_ms": 35
  }
}
```

**Fields:**
- `keywords` (array): Top keywords with scores
- `entities` (array): Named entities with types
- `sentiment` (object): Overall sentiment analysis
- `latency_ms` (int): NLP processing time

#### 5. Summary Results

**Server → Client: Summary**
```json
{
  "type": "summary",
  "timestamp": 1732411200400,
  "session_id": "sess_abc123def456",
  "payload": {
    "summary": "A brief summary of the transcription.",
    "cache_hit": false,
    "summary_length": 12,
    "original_length": 45,
    "compression_ratio": 0.27,
    "latency_ms": 165
  }
}
```

**Fields:**
- `summary` (string): Generated summary text
- `cache_hit` (boolean): Whether from cache
- `summary_length` (int): Word count of summary
- `original_length` (int): Word count of original
- `compression_ratio` (float): Summary/original length ratio
- `latency_ms` (int): Generation time (includes cache check)

#### 6. Aggregated Results

**Server → Client: Combined Result**
```json
{
  "type": "result",
  "timestamp": 1732411200400,
  "session_id": "sess_abc123def456",
  "payload": {
    "transcription": {
      "text": "Hello, this is a test",
      "confidence": 0.92,
      "latency_ms": 285
    },
    "insights": {
      "keywords": [
        {
          "keyword": "test",
          "score": 0.95
        }
      ],
      "sentiment": {
        "polarity": "POSITIVE",
        "score": 0.75
      },
      "latency_ms": 35
    },
    "summary": {
      "text": "A brief summary.",
      "cache_hit": false,
      "latency_ms": 165
    },
    "total_latency_ms": 320
  }
}
```

#### 7. Error Messages

**Server → Client: Error**
```json
{
  "type": "error",
  "timestamp": 1732411200500,
  "session_id": "sess_abc123def456",
  "payload": {
    "error_code": "SERVICE_UNAVAILABLE",
    "message": "Summary service temporarily unavailable",
    "service": "summary",
    "recoverable": true,
    "retry_after_ms": 5000
  }
}
```

**Error Codes:**
- `INVALID_AUDIO`: Audio data format invalid
- `AUDIO_TOO_LARGE`: Audio chunk exceeds max size
- `SERVICE_UNAVAILABLE`: Backend service down
- `TIMEOUT`: Request took too long
- `QUOTA_EXCEEDED`: Token/request quota exceeded
- `INTERNAL_ERROR`: Unexpected server error

#### 8. Connection Control

**Client → Server: Disconnect**
```json
{
  "type": "session_end",
  "timestamp": 1732411200600,
  "session_id": "sess_abc123def456",
  "payload": {
    "reason": "user_requested"
  }
}
```

**Server → Client: Disconnect Confirmation**
```json
{
  "type": "session_ended",
  "timestamp": 1732411200601,
  "session_id": "sess_abc123def456",
  "payload": {
    "status": "closed",
    "duration_ms": 400,
    "total_chunks": 2,
    "total_results": 2
  }
}
```

### Connection Lifecycle

```
1. Client connects to ws://localhost:8000/ws
2. Client sends "session_start" message
3. Server responds with "session_started"
4. Client sends audio chunks via "audio_chunk" messages
5. Server sends back transcription, insights, summaries
6. Client sends "session_end" when done
7. Server confirms with "session_ended"
8. Connection closes
```

### JavaScript Example

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');

  // Start session
  ws.send(JSON.stringify({
    type: 'session_start',
    timestamp: Date.now(),
    payload: {
      language: 'en-US',
      enable_nlp: true,
      enable_summary: true
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch(message.type) {
    case 'session_started':
      console.log('Session started:', message.session_id);
      // Ready to send audio
      break;

    case 'transcription':
      console.log('Transcription:', message.payload.text);
      break;

    case 'nlp_insights':
      console.log('Keywords:', message.payload.keywords);
      break;

    case 'summary':
      console.log('Summary:', message.payload.summary);
      break;

    case 'error':
      console.error('Error:', message.payload.message);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};

// Send audio chunk
function sendAudioChunk(audioData) {
  ws.send(JSON.stringify({
    type: 'audio_chunk',
    timestamp: Date.now(),
    session_id: sessionId,
    payload: {
      audio_data: btoa(audioData), // base64 encode
      sample_rate: 16000,
      channels: 1,
      format: 'PCM_16'
    }
  }));
}
```

---

## REST API

### Base URL

`http://localhost:8000`

### Authentication

None required (add JWT token in production)

### Response Format

All responses are JSON:

```json
{
  "status": "success|error",
  "data": {},
  "error": null,
  "timestamp": "2025-11-24T10:00:00Z"
}
```

### Endpoints

#### 1. Health Check

**GET** `/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "services": {
    "backend": "healthy",
    "stt": "healthy",
    "nlp": "healthy",
    "summary": "healthy",
    "redis": "healthy"
  },
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Status Values:** `healthy`, `degraded`, `unhealthy`

#### 2. Service Health Details

**GET** `/health/services`

**Response (200 OK):**
```json
{
  "services": {
    "stt-engine": {
      "status": "healthy",
      "latency_ms": 285,
      "uptime_hours": 24
    },
    "nlp-service": {
      "status": "healthy",
      "latency_ms": 35,
      "uptime_hours": 24
    },
    "summary-service": {
      "status": "healthy",
      "latency_ms": 165,
      "cache_hit_rate": 0.72,
      "uptime_hours": 24
    }
  }
}
```

#### 3. List Sessions

**GET** `/api/v1/sessions`

**Query Parameters:**
- `limit` (int): Max results (default: 100)
- `offset` (int): Pagination offset (default: 0)
- `status` (string): Filter by status (active, completed, failed)

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "id": "sess_abc123def456",
      "created_at": "2025-11-24T10:00:00Z",
      "duration_ms": 5000,
      "status": "completed",
      "audio_chunks": 5,
      "transcription_count": 5,
      "language": "en-US"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### 4. Get Session Details

**GET** `/api/v1/sessions/{session_id}`

**Response (200 OK):**
```json
{
  "session": {
    "id": "sess_abc123def456",
    "created_at": "2025-11-24T10:00:00Z",
    "duration_ms": 5000,
    "status": "completed",
    "metadata": {
      "language": "en-US",
      "device": "microphone_1",
      "client_version": "1.0.0"
    },
    "statistics": {
      "audio_chunks": 5,
      "total_audio_seconds": 10.0,
      "transcriptions": 5,
      "avg_confidence": 0.91
    }
  }
}
```

#### 5. Get Transcription

**GET** `/api/v1/sessions/{session_id}/transcript`

**Query Parameters:**
- `format` (string): `text`, `json`, `srt`, `vtt` (default: `json`)

**Response (200 OK - JSON format):**
```json
{
  "transcription": {
    "full_text": "Hello, this is a test. This is the second sentence.",
    "segments": [
      {
        "start_time": 0.0,
        "end_time": 2.5,
        "text": "Hello, this is a test.",
        "confidence": 0.92
      },
      {
        "start_time": 2.5,
        "end_time": 5.0,
        "text": "This is the second sentence.",
        "confidence": 0.89
      }
    ],
    "language": "en",
    "duration_ms": 5000
  }
}
```

**Response (200 OK - Text format):**
```
Hello, this is a test. This is the second sentence.
```

**Response (200 OK - SRT format):**
```
1
00:00:00,000 --> 00:00:02,500
Hello, this is a test.

2
00:00:02,500 --> 00:00:05,000
This is the second sentence.
```

#### 6. Get Summary

**GET** `/api/v1/sessions/{session_id}/summary`

**Response (200 OK):**
```json
{
  "summary": {
    "text": "The user tested the microphone and confirmed it was working.",
    "length": 12,
    "original_length": 45,
    "compression_ratio": 0.27,
    "cache_hit": false,
    "generated_at": "2025-11-24T10:00:03Z"
  }
}
```

#### 7. Get NLP Insights

**GET** `/api/v1/sessions/{session_id}/insights`

**Response (200 OK):**
```json
{
  "insights": {
    "keywords": [
      {
        "keyword": "test",
        "score": 0.95
      },
      {
        "keyword": "microphone",
        "score": 0.88
      }
    ],
    "entities": [
      {
        "text": "test",
        "type": "EVENT",
        "confidence": 0.85
      }
    ],
    "sentiment": {
      "polarity": "NEUTRAL",
      "score": 0.5
    },
    "language": "en"
  }
}
```

#### 8. Delete Session

**DELETE** `/api/v1/sessions/{session_id}`

**Response (200 OK):**
```json
{
  "status": "deleted",
  "session_id": "sess_abc123def456"
}
```

#### 9. Get Metrics

**GET** `/metrics`

**Format:** Prometheus text format

**Sample Output:**
```
# HELP rtstt_stt_latency_ms Speech-to-text latency in milliseconds
# TYPE rtstt_stt_latency_ms histogram
rtstt_stt_latency_ms_bucket{le="50"} 0
rtstt_stt_latency_ms_bucket{le="100"} 0
rtstt_stt_latency_ms_bucket{le="200"} 5
rtstt_stt_latency_ms_bucket{le="300"} 18
rtstt_stt_latency_ms_bucket{le="500"} 42

# HELP rtstt_nlp_latency_ms NLP processing latency
# TYPE rtstt_nlp_latency_ms histogram
rtstt_nlp_latency_ms_bucket{le="10"} 2
rtstt_nlp_latency_ms_bucket{le="50"} 38
rtstt_nlp_latency_ms_bucket{le="100"} 42

# HELP rtstt_summary_cache_hits Cache hit counter
# TYPE rtstt_summary_cache_hits counter
rtstt_summary_cache_hits_total 72

# HELP rtstt_active_sessions Active session count
# TYPE rtstt_active_sessions gauge
rtstt_active_sessions 0
```

#### 10. API Documentation

**GET** `/docs` - Interactive Swagger UI

**GET** `/redoc` - ReDoc documentation

---

## gRPC API - NLP Service

### Service: NLPService

**Port:** 50052
**Proto:** `protos/nlp_service.proto`

### RPC Methods

#### ExtractInsights

Extracts keywords, entities, and sentiment from text.

**Request:**
```protobuf
message TranscriptionRequest {
  string text = 1;           // Text to analyze
  string session_id = 2;     // Session identifier
  int32 top_keywords = 3;    // Number of top keywords to return (default: 10)
}
```

**Response:**
```protobuf
message InsightsResponse {
  repeated Keyword keywords = 1;    // Extracted keywords
  repeated Entity entities = 2;     // Named entities
  Sentiment sentiment = 3;          // Overall sentiment
  int32 latency_ms = 4;             // Processing latency
}

message Keyword {
  string keyword = 1;     // The keyword
  float score = 2;        // Score (0.0 - 1.0)
}

message Entity {
  string text = 1;           // Entity text
  string type = 2;           // Entity type (PERSON, ORG, LOCATION, MISC, etc.)
  float confidence = 3;      // Confidence score
}

message Sentiment {
  string polarity = 1;   // POSITIVE, NEGATIVE, NEUTRAL
  float score = 2;       // Score (-1.0 to 1.0)
}
```

**Python Example:**
```python
import grpc
from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc

def extract_insights(text: str):
    channel = grpc.insecure_channel('localhost:50052')
    stub = nlp_service_pb2_grpc.NLPServiceStub(channel)

    request = nlp_service_pb2.TranscriptionRequest(
        text=text,
        session_id="session_001",
        top_keywords=10
    )

    response = stub.ExtractInsights(request)

    print(f"Keywords: {[kw.keyword for kw in response.keywords]}")
    print(f"Entities: {[(e.text, e.type) for e in response.entities]}")
    print(f"Sentiment: {response.sentiment.polarity} ({response.sentiment.score})")
    print(f"Latency: {response.latency_ms}ms")

    return response
```

#### HealthCheck

Checks service availability.

**Request:**
```protobuf
message Empty {}
```

**Response:**
```protobuf
message HealthCheckResponse {
  string status = 1;  // SERVING, NOT_SERVING, UNKNOWN
}
```

**Curl Example:**
```bash
grpc_health_probe -addr=localhost:50052
# Output: status: SERVING
```

---

## gRPC API - Summary Service

### Service: SummaryService

**Port:** 50053
**Proto:** `protos/summary_service.proto`

### RPC Methods

#### GenerateSummary

Generates a summary for the given text.

**Request:**
```protobuf
message TextRequest {
  string text = 1;               // Text to summarize
  string session_id = 2;         // Session identifier
  int32 max_length = 3;          // Max summary length (default: 100)
  float temperature = 4;         // Output randomness (default: 0.7)
}
```

**Response:**
```protobuf
message SummaryResponse {
  string summary = 1;            // Generated summary
  bool cache_hit = 2;            // Whether from cache
  int32 latency_ms = 3;          // Processing latency
  string cache_key = 4;          // Cache key used (for debugging)
}
```

**Python Example:**
```python
import grpc
from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

def generate_summary(text: str):
    channel = grpc.insecure_channel('localhost:50053')
    stub = summary_service_pb2_grpc.SummaryServiceStub(channel)

    request = summary_service_pb2.TextRequest(
        text=text,
        session_id="session_001",
        max_length=100,
        temperature=0.7
    )

    response = stub.GenerateSummary(request)

    print(f"Summary: {response.summary}")
    print(f"Cache hit: {response.cache_hit}")
    print(f"Latency: {response.latency_ms}ms")

    return response
```

#### GenerateSummaryBatch

Generates summaries for multiple texts in batch.

**Request:**
```protobuf
message BatchTextRequest {
  repeated TextRequest requests = 1;  // Up to 32 requests
}
```

**Response:**
```protobuf
message BatchSummaryResponse {
  repeated SummaryResponse responses = 1;  // Parallel responses
}
```

**Python Example:**
```python
def batch_summarize(texts: list):
    channel = grpc.insecure_channel('localhost:50053')
    stub = summary_service_pb2_grpc.SummaryServiceStub(channel)

    requests = [
        summary_service_pb2.TextRequest(
            text=text,
            session_id="session_001",
            max_length=100
        )
        for text in texts
    ]

    batch_request = summary_service_pb2.BatchTextRequest(
        requests=requests
    )

    batch_response = stub.GenerateSummaryBatch(batch_request)

    for response in batch_response.responses:
        print(f"Summary: {response.summary}")
        print(f"Cache hit: {response.cache_hit}")
```

#### HealthCheck

Checks service availability and cache connectivity.

**Response Indicates:**
- Service running and responding
- Redis cache accessible
- Model loaded and ready

---

## gRPC API - STT Service

### Service: STTService

**Port:** 50051
**Proto:** `protos/stt_service.proto`

### RPC Methods

#### Transcribe

Transcribes audio to text using Whisper model.

**Request:**
```protobuf
message AudioRequest {
  bytes audio_data = 1;      // WAV or PCM audio
  string language = 2;       // Language code (e.g., "en", "it", "auto")
  string model = 3;          // Model size (tiny, base, small, medium, large-v3)
}
```

**Response:**
```protobuf
message TranscriptionResponse {
  string text = 1;           // Transcribed text
  float confidence = 2;      // Confidence score (0.0 - 1.0)
  int32 latency_ms = 3;      // Processing latency
  string language = 4;       // Detected language
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | OK | Request successful |
| 400 | Bad Request | Check parameters |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Retry later |

### gRPC Status Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | OK | Success |
| 3 | INVALID_ARGUMENT | Bad input |
| 4 | DEADLINE_EXCEEDED | Timeout |
| 5 | NOT_FOUND | Resource not found |
| 14 | UNAVAILABLE | Service down |
| 13 | INTERNAL | Server error |

### Error Response Format

**REST:**
```json
{
  "status": "error",
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Summary service is unavailable",
    "details": {
      "service": "summary",
      "timestamp": "2025-11-24T10:00:00Z"
    }
  }
}
```

**gRPC:**
```python
try:
    response = stub.GenerateSummary(request)
except grpc.RpcError as e:
    print(f"Code: {e.code()}")
    print(f"Details: {e.details()}")
```

### Retry Strategy

Recommended exponential backoff:
```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
```

---

## Code Examples

### Complete WebSocket Client (JavaScript)

```javascript
class RTSTTClient {
  constructor(url = 'ws://localhost:8000/ws') {
    this.url = url;
    this.ws = null;
    this.sessionId = null;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => this.onConnected();
    this.ws.onmessage = (e) => this.onMessage(e);
    this.ws.onerror = (e) => this.onError(e);
    this.ws.onclose = () => this.onClosed();
  }

  onConnected() {
    console.log('Connected to RTSTT');
    this.send({
      type: 'session_start',
      timestamp: Date.now(),
      payload: {
        language: 'en-US',
        enable_nlp: true,
        enable_summary: true
      }
    });
  }

  onMessage(event) {
    const message = JSON.parse(event.data);

    switch(message.type) {
      case 'session_started':
        this.sessionId = message.session_id;
        console.log('Session started:', this.sessionId);
        break;

      case 'transcription':
        console.log('Transcription:', message.payload.text);
        break;

      case 'nlp_insights':
        console.log('Keywords:', message.payload.keywords);
        break;

      case 'summary':
        console.log('Summary:', message.payload.summary);
        break;

      case 'error':
        console.error('Error:', message.payload.message);
        break;
    }
  }

  onError(error) {
    console.error('WebSocket error:', error);
  }

  onClosed() {
    console.log('Connection closed');
  }

  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  sendAudio(audioData) {
    this.send({
      type: 'audio_chunk',
      timestamp: Date.now(),
      session_id: this.sessionId,
      payload: {
        audio_data: btoa(audioData),
        sample_rate: 16000,
        channels: 1,
        format: 'PCM_16'
      }
    });
  }

  close() {
    this.send({
      type: 'session_end',
      timestamp: Date.now(),
      session_id: this.sessionId,
      payload: { reason: 'user_requested' }
    });
  }
}

// Usage
const client = new RTSTTClient();
client.connect();
```

### gRPC Client (Python)

```python
import grpc
from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc
from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc

class RTSTTGRPCClient:
    def __init__(self, nlp_host='localhost', nlp_port=50052,
                 summary_host='localhost', summary_port=50053):
        self.nlp_channel = grpc.insecure_channel(f'{nlp_host}:{nlp_port}')
        self.nlp_stub = nlp_service_pb2_grpc.NLPServiceStub(self.nlp_channel)

        self.summary_channel = grpc.insecure_channel(f'{summary_host}:{summary_port}')
        self.summary_stub = summary_service_pb2_grpc.SummaryServiceStub(self.summary_channel)

    def extract_insights(self, text, top_keywords=10):
        request = nlp_service_pb2.TranscriptionRequest(
            text=text,
            session_id="session_001",
            top_keywords=top_keywords
        )
        return self.nlp_stub.ExtractInsights(request)

    def generate_summary(self, text, max_length=100):
        request = summary_service_pb2.TextRequest(
            text=text,
            session_id="session_001",
            max_length=max_length
        )
        return self.summary_stub.GenerateSummary(request)

    def check_nlp_health(self):
        try:
            response = self.nlp_stub.HealthCheck(nlp_service_pb2.Empty())
            return response.status == 'SERVING'
        except grpc.RpcError:
            return False

    def close(self):
        self.nlp_channel.close()
        self.summary_channel.close()

# Usage
client = RTSTTGRPCClient()

# Extract insights
response = client.extract_insights("Hello, this is a test")
print("Keywords:", [kw.keyword for kw in response.keywords])

# Generate summary
summary = client.generate_summary("This is a longer text...")
print("Summary:", summary.summary)

client.close()
```

---

**For deployment information, see:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**For architecture details, see:** [ARCHITECTURE.md](ARCHITECTURE.md)
**For testing procedures, see:** [TESTING_GUIDE.md](TESTING_GUIDE.md)
