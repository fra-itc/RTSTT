# RTSTT Deployment Guide (Wave 4A)

**Step-by-step instructions for deploying Real-Time Speech-to-Text with production gRPC services**

**Version:** 1.0
**Last Updated:** November 24, 2025
**Target Audience:** DevOps engineers, system administrators, developers

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Service Startup Sequence](#service-startup-sequence)
5. [Health Checks](#health-checks)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [Production Considerations](#production-considerations)
9. [Monitoring Setup](#monitoring-setup)
10. [Rollback Procedure](#rollback-procedure)

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 8 cores, 3.0 GHz
- RAM: 32 GB
- GPU: NVIDIA RTX 5080 (16 GB VRAM) or compatible
- Storage: 100 GB SSD
- Network: 1 Gbps Ethernet

**Recommended:**
- CPU: 16+ cores
- RAM: 64 GB
- GPU: 2x NVIDIA RTX 5080
- Storage: 500 GB SSD (RAID 1)
- Network: 10 Gbps Ethernet

### Software Requirements

**Core:**
- Docker: 24.0+ with NVIDIA Container Runtime
- Docker Compose: 2.0+
- NVIDIA Driver: 576.88+ (CUDA 12.8 support)
- CUDA: 12.8.0
- cuDNN: 8.9.0+
- Python: 3.10+ (for host utilities only)

**Optional:**
- Node.js: 18+ (for frontend development)
- Git: 2.25+
- kubectl: 1.26+ (for Kubernetes deployment)

### System Checks

```bash
# Check Docker installation
docker --version
# Expected: Docker version 24.0 or higher

# Check NVIDIA Driver
nvidia-smi
# Expected: CUDA Version 12.8

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi
# Expected: RTX 5080 detected, CUDA 12.8

# Check available storage
df -h
# Expected: >100GB free on root partition

# Check network connectivity
ping 8.8.8.8 -c 1
# Expected: Successful response
```

---

## System Requirements

### Supported Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| Ubuntu 22.04 LTS | ✅ Recommended | Fully tested |
| Ubuntu 20.04 LTS | ✅ Supported | May need older Docker |
| Debian 11+ | ✅ Supported | Same as Ubuntu |
| CentOS/RHEL 8+ | ✅ Supported | Use DNF instead of apt |
| Windows 11 WSL2 | ✅ Supported | Use WebSocket audio bridge |
| macOS | ⚠️ Experimental | PortAudio required |

### Port Requirements

| Port | Service | Protocol | Required |
|------|---------|----------|----------|
| 8000 | Backend API | HTTP | Yes |
| 50051 | STT Service | gRPC | Yes |
| 50052 | NLP Service | gRPC | Yes |
| 50053 | Summary Service | gRPC | Yes |
| 6379 | Redis | Redis | Yes |
| 9090 | Prometheus | HTTP | No |
| 3001 | Grafana | HTTP | No |

**Network Security:**
- All ports should be restricted to trusted networks
- Use firewall rules to limit access
- Run behind reverse proxy in production

### Environment Variables

**Required:**
```bash
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility
export CUDA_VISIBLE_DEVICES=0      # Single GPU setup
export DEVICE=cuda                 # Use GPU
```

**Optional:**
```bash
export HF_TOKEN=<your-huggingface-token>  # For model downloads
export REDIS_PASSWORD=<secure-password>    # For authentication
export LOG_LEVEL=INFO                      # For debugging
```

---

## Installation Steps

### Step 1: System Preparation

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install prerequisites
sudo apt-get install -y \
    curl \
    wget \
    git \
    jq \
    net-tools \
    htop \
    build-essential

# Create project directory
mkdir -p /opt/rtstt
cd /opt/rtstt

# Set permissions
sudo chown -R $USER:$USER /opt/rtstt
```

### Step 2: Docker & NVIDIA Setup

```bash
# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.8.0-runtime-ubuntu22.04 nvidia-smi
```

### Step 3: Clone Repository

```bash
cd /opt/rtstt

# Clone the repository
git clone https://github.com/your-org/RTSTT.git .

# Checkout Wave 4A branch
git checkout feature/track2-grpc-services

# Verify directory structure
ls -la
# Expected: docs/ src/ tests/ docker-compose.yml .env.example etc.
```

### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file with production values
vim .env

# Required settings:
# - DEVICE=cuda
# - REDIS_PASSWORD=<secure-password>
# - HF_TOKEN=<your-huggingface-token>
# - LOG_LEVEL=INFO
# - STT_SERVICE_HOST=stt-engine
# - NLP_SERVICE_HOST=nlp-service
# - SUMMARY_SERVICE_HOST=summary-service
```

### Step 5: Build Docker Images

```bash
# Pull base images (large files ~20GB)
docker pull nvidia/cuda:12.8.0-runtime-ubuntu22.04

# Build all services
docker-compose build --no-cache

# Verify images
docker images | grep rtstt
# Expected: All services built successfully

# Size check (optional)
docker images | awk '{if (NR > 1) print $1, $7}'
# Expected: Each image ~11GB
```

### Step 6: Start Infrastructure Services

```bash
# Start Redis (required for all services)
docker-compose up -d redis

# Wait for Redis to be ready
sleep 5
docker-compose exec redis redis-cli ping
# Expected: PONG

# Start monitoring stack (optional but recommended)
docker-compose up -d prometheus grafana

# Verify infrastructure
docker-compose ps
# Expected: redis, prometheus, grafana running
```

### Step 7: Start ML Services

```bash
# Start STT Engine (largest, takes longer)
docker-compose up -d stt-engine
# Wait for startup (~60 seconds)
sleep 60

# Start NLP Service
docker-compose up -d nlp-service
sleep 30

# Start Summary Service
docker-compose up -d summary-service
sleep 30

# Verify services started
docker-compose ps
# Expected: All services in 'Up' state

# Check logs for errors
docker-compose logs stt-engine | tail -20
docker-compose logs nlp-service | tail -20
docker-compose logs summary-service | tail -20
```

### Step 8: Start Backend Gateway

```bash
# Start backend
docker-compose up -d backend

# Wait for startup
sleep 10

# Verify backend is responding
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

# Check logs
docker-compose logs backend | tail -20
```

### Step 9: Deploy Frontend (Optional)

```bash
# Navigate to UI directory
cd src/ui

# Install dependencies
npm install

# Build production version
npm run build:all

# Start application
npm start

# Or for development with hot reload
npm run dev
```

### Step 10: Verify Complete Setup

```bash
# Check all services are healthy
curl http://localhost:8000/health/services

# Check individual gRPC services
docker-compose exec backend grpc_health_probe -addr=localhost:50051
docker-compose exec backend grpc_health_probe -addr=localhost:50052
docker-compose exec backend grpc_health_probe -addr=localhost:50053

# Test end-to-end latency
pytest tests/test_grpc_services_integration.py::test_end_to_end_pipeline -v

# Access monitoring dashboards
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3001"
echo "Backend API: http://localhost:8000/docs"
```

---

## Service Startup Sequence

**Important:** Services must start in this order for proper initialization.

```
1. Redis (port 6379)
   ↓
2. STT Engine (port 50051) - 60 seconds startup
   ↓
3. NLP Service (port 50052) - 30 seconds startup
   ↓
4. Summary Service (port 50053) - 30 seconds startup
   ↓
5. Backend Gateway (port 8000)
   ↓
6. Monitoring Stack (optional)
   ↓
7. Frontend (optional)
```

### Automated Startup Script

```bash
#!/bin/bash
# scripts/start-services.sh

set -e

echo "Starting RTSTT services..."

# 1. Start Redis
echo "1. Starting Redis..."
docker-compose up -d redis
sleep 5

# 2. Start ML Services
echo "2. Starting STT Engine..."
docker-compose up -d stt-engine
sleep 60

echo "3. Starting NLP Service..."
docker-compose up -d nlp-service
sleep 30

echo "4. Starting Summary Service..."
docker-compose up -d summary-service
sleep 30

# 3. Start Backend
echo "5. Starting Backend..."
docker-compose up -d backend
sleep 10

# 4. Start monitoring (optional)
echo "6. Starting monitoring stack..."
docker-compose up -d prometheus grafana
sleep 10

# Verify all services
echo "Checking service health..."
curl http://localhost:8000/health || echo "Backend health check failed"

echo "All services started!"
docker-compose ps
```

---

## Health Checks

### Service Health Status

**Check overall system health:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "services": {
    "stt": "healthy",
    "nlp": "healthy",
    "summary": "healthy",
    "redis": "healthy"
  },
  "timestamp": "2025-11-24T10:00:00Z"
}
```

### Individual Service Health

**STT Engine:**
```bash
docker-compose exec backend grpc_health_probe -addr=stt-engine:50051
# Expected: status: SERVING
```

**NLP Service:**
```bash
docker-compose exec backend grpc_health_probe -addr=nlp-service:50052
# Expected: status: SERVING
```

**Summary Service:**
```bash
docker-compose exec backend grpc_health_probe -addr=summary-service:50053
# Expected: status: SERVING
```

**Redis:**
```bash
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### Performance Health Checks

```bash
# STT latency check
time curl -X POST http://localhost:8000/api/v1/test/stt \
  -H "Content-Type: application/json" \
  -d '{"audio_data": "..."}'
# Expected: <300ms

# End-to-end latency check
pytest tests/test_grpc_services_integration.py::test_end_to_end_pipeline -v
# Expected: 253-312ms total latency
```

### Automated Health Monitoring

**Prometheus queries for alerting:**
```promql
# Alert if service down for >5 minutes
up{job="stt-service"} == 0 for 5m

# Alert if latency exceeds threshold
rate(rtstt_stt_latency_ms[5m]) > 300

# Alert if cache hit rate too low
rate(rtstt_summary_cache_misses[5m]) /
  (rate(rtstt_summary_cache_hits[5m]) + rate(rtstt_summary_cache_misses[5m])) > 0.5
```

---

## Configuration

### Environment Variables

**Backend Configuration:**
```bash
# Service hosts (use Docker Compose service names internally)
STT_SERVICE_HOST=stt-engine
STT_SERVICE_PORT=50051
NLP_SERVICE_HOST=nlp-service
NLP_SERVICE_PORT=50052
SUMMARY_SERVICE_HOST=summary-service
SUMMARY_SERVICE_PORT=50053

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<if-set>
REDIS_DB=0

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
API_TITLE=RTSTT
API_VERSION=1.0.0
API_DOCS_URL=/docs

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_CREDENTIALS=true

# Timeouts
GRPC_TIMEOUT=30
WEBSOCKET_TIMEOUT=300

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=8001
```

**STT Service Configuration:**
```bash
DEVICE=cuda
MODEL_NAME=whisper-large-v3
FP16=true
GPU_MEMORY_FRACTION=0.7
BATCH_SIZE=1
LANGUAGE=auto  # auto-detect

# Hugging Face
HF_TOKEN=<your-token>
HF_HOME=/models
```

**NLP Service Configuration:**
```bash
DEVICE=cuda
MODEL_NAME=all-MiniLM-L6-v2
NER_MODEL=dbmdz/bert-base-multilingual-uncased
TOP_KEYWORDS=10
BATCH_SIZE=32

HF_TOKEN=<your-token>
HF_HOME=/models
```

**Summary Service Configuration:**
```bash
DEVICE=cuda
MODEL_NAME=meta-llama/Llama-3.2-8B-Instruct
MAX_LENGTH=100
TEMPERATURE=0.7
QUANTIZATION=true

REDIS_HOST=redis
REDIS_PORT=6379
CACHE_TTL=3600

HF_TOKEN=<your-token>
HF_HOME=/models
```

### Docker Compose Override

**For production customization, create `docker-compose.override.yml`:**
```yaml
version: '3.8'

services:
  backend:
    ports:
      - "8000:8000"
      - "8001:8001"  # metrics
    environment:
      LOG_LEVEL: WARNING
      GRPC_TIMEOUT: 60

  stt-engine:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 12G
    environment:
      GPU_MEMORY_FRACTION: 0.8

  prometheus:
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    environment:
      GF_SECURITY_ADMIN_PASSWORD: <secure-password>
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## Troubleshooting

### Service Won't Start

**Symptom:** Container exits immediately

**Diagnosis:**
```bash
docker-compose logs <service-name>
```

**Common Issues:**

1. **Port already in use:**
```bash
# Check port
sudo lsof -i :50051
# Kill process
sudo kill -9 <PID>
```

2. **Insufficient GPU memory:**
```bash
nvidia-smi
# Expected: 16GB available on RTX 5080
```

3. **Missing environment variables:**
```bash
docker-compose config | grep -i error
```

### Connection Refused

**Symptom:** Backend can't connect to gRPC services

**Diagnosis:**
```bash
# Check if service is running
docker-compose ps

# Check if port is listening
netstat -tuln | grep 5005

# Check Docker network
docker network ls
docker network inspect rtstt_default
```

**Solution:**
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Verify connectivity from backend
docker-compose exec backend ping stt-engine
docker-compose exec backend netcat -zv stt-engine 50051
```

### High Memory Usage

**Symptom:** Docker containers consuming >14GB

**Diagnosis:**
```bash
docker stats

# Check GPU memory
docker-compose exec stt-engine nvidia-smi
```

**Solutions:**
1. Reduce batch size
2. Reduce model size (use smaller variant)
3. Increase available GPU memory

### Slow Performance

**Symptom:** Latency >500ms

**Diagnosis:**
```bash
# Check service latencies
curl http://localhost:8000/metrics | grep latency

# Check Redis
docker-compose exec redis redis-cli info stats
```

**Solutions:**
1. Verify GPU is being used (nvidia-smi)
2. Check Redis connectivity
3. Monitor CPU/memory utilization
4. Check network latency

### WebSocket Connection Failed

**Symptom:** Frontend can't connect to backend

**Diagnosis:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8000/ws
```

**Solutions:**
1. Ensure backend is running: `docker-compose up -d backend`
2. Check firewall: `sudo ufw allow 8000`
3. Verify URL in frontend config
4. Check logs: `docker-compose logs backend`

---

## Production Considerations

### Security

**1. Network Isolation:**
```bash
# Run on private network only
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Or use reverse proxy
# - Nginx: proxy_pass http://localhost:8000
# - HAProxy: balance roundrobin
```

**2. TLS/HTTPS:**
```yaml
# In docker-compose.yml, add SSL certificates
volumes:
  - /etc/ssl/certs:/etc/ssl/certs:ro
  - /etc/ssl/private:/etc/ssl/private:ro
```

**3. Authentication:**
```bash
# Add JWT validation
export JWT_SECRET=<secure-random-string>
export JWT_ALGORITHM=HS256
```

### Scaling

**For 1000+ concurrent users:**
```yaml
# Use multiple backend instances behind load balancer
backend-1:
  image: rtstt/backend:latest
  port: 8001

backend-2:
  image: rtstt/backend:latest
  port: 8002

# Use Nginx for load balancing
upstream backend {
  server backend-1:8000;
  server backend-2:8000;
}
```

### Backup & Recovery

**Backup Redis data:**
```bash
# Manual backup
docker-compose exec redis redis-cli BGSAVE

# Verify backup
docker-compose exec redis ls -la /data/dump.rdb

# Automated daily backup
0 2 * * * docker-compose exec redis redis-cli BGSAVE && \
            cp /var/lib/docker/volumes/*/_data/dump.rdb /backups/redis-$(date +%s).rdb
```

**Restore from backup:**
```bash
docker-compose down
cp /backups/redis-<timestamp>.rdb <redis-volume>/dump.rdb
docker-compose up -d redis
```

### Monitoring & Logging

**Centralized logging:**
```yaml
# Add to docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

# Configure log drivers
services:
  backend:
    logging:
      driver: loki
      options:
        loki-url: http://loki:3100/loki/api/v1/push
```

**Log aggregation queries:**
```promql
# Errors in past hour
{job="backend"} |= "ERROR" | timestamp > now-1h

# Performance issues
{job="stt-service"} |= "latency" > 300
```

### Disaster Recovery Plan

| Scenario | RTO | Solution |
|----------|-----|----------|
| Service crash | <5 min | Docker Compose auto-restart |
| Disk full | <30 min | Expand volume, cleanup old logs |
| GPU failure | <60 min | Switch to secondary GPU |
| Network partition | <2 min | Health checks + failover |
| Data loss | <1 hour | Restore from backup |

---

## Monitoring Setup

### Prometheus Configuration

**Default scrape targets:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'rtstt-backend'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'stt-service'
    static_configs:
      - targets: ['localhost:50051']

  - job_name: 'nlp-service'
    static_configs:
      - targets: ['localhost:50052']

  - job_name: 'summary-service'
    static_configs:
      - targets: ['localhost:50053']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
```

### Grafana Dashboards

**Import dashboards:**
1. Open Grafana: http://localhost:3001
2. Go to Dashboards → Import
3. Upload JSON from `monitoring/dashboards/`

**Key metrics to monitor:**
- Backend latency (p50, p95, p99)
- Service availability (uptime %)
- GPU memory usage
- Cache hit rate
- Error rate

### Alerting Rules

**Example alert configuration:**
```yaml
# prometheus-rules.yml
groups:
  - name: rtstt-alerts
    rules:
      - alert: STTServiceDown
        expr: up{job="stt-service"} == 0
        for: 5m
        annotations:
          summary: "STT service is down"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rtstt_stt_latency_ms) > 400
        for: 10m
        annotations:
          summary: "STT latency exceeds threshold"

      - alert: LowCacheHitRate
        expr: |
          rate(rtstt_summary_cache_hits[5m]) /
          (rate(rtstt_summary_cache_hits[5m]) + rate(rtstt_summary_cache_misses[5m])) < 0.5
        for: 30m
        annotations:
          summary: "Summary cache hit rate below 50%"
```

---

## Rollback Procedure

### If Something Goes Wrong

**1. Stop all services:**
```bash
docker-compose down
```

**2. Revert to previous version:**
```bash
git log --oneline | head -5
git checkout <previous-commit-hash>
docker-compose build --no-cache
```

**3. Restore Redis data:**
```bash
# From backup
cp /backups/redis-<previous>.rdb <redis-volume>/dump.rdb
```

**4. Restart services:**
```bash
docker-compose up -d
```

**5. Verify health:**
```bash
curl http://localhost:8000/health
docker-compose ps
```

### Version Management

**Keep multiple versions:**
```bash
# Tag each release
git tag -a v4a-release-2025-11-24 -m "Wave 4A Production Release"
git push origin v4a-release-2025-11-24

# Quick rollback
git checkout v4a-release-2025-11-24
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start all services | `docker-compose up -d` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f <service>` |
| Check health | `curl http://localhost:8000/health` |
| Restart service | `docker-compose restart <service>` |
| View metrics | `http://localhost:9090` |
| View dashboards | `http://localhost:3001` |
| Test API | `curl http://localhost:8000/docs` |

---

**For architecture details, see:** [ARCHITECTURE.md](ARCHITECTURE.md)
**For API documentation, see:** [API_REFERENCE.md](API_REFERENCE.md)
**For testing procedures, see:** [TESTING_GUIDE.md](TESTING_GUIDE.md)
