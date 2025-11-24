# Backend Rebuild Checklist

**Purpose:** Add Prometheus instrumentation to backend for metrics collection

**Status:** Pre-rebuild testing complete, all systems operational

## Files to Modify

### 1. requirements.txt

**Location:** `/home/frisco/projects/RTSTT/requirements.txt`

**Change:** Add Prometheus client library

```diff
+ prometheus-client>=0.19.0
```

### 2. src/agents/orchestrator/fastapi_app.py

**Location:** `/home/frisco/projects/RTSTT/src/agents/orchestrator/fastapi_app.py`

**Changes Required:**

#### Add Imports
```python
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
```

#### Add Metrics Definitions (after imports)
```python
# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# WebSocket metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['type']
)

# gRPC metrics
grpc_requests_total = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['service', 'method', 'status']
)

grpc_request_duration_seconds = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request latency',
    ['service', 'method']
)
```

#### Add Metrics Endpoint (before app initialization)
```python
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from starlette.responses import Response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

#### Add Middleware (after app initialization)
```python
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Collect metrics for HTTP requests"""
    method = request.method
    endpoint = request.url.path

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

    return response
```

### 3. src/shared/protocols/grpc_pool.py (Optional but Recommended)

**Location:** `/home/frisco/projects/RTSTT/src/shared/protocols/grpc_pool.py`

**Change:** Adjust keepalive settings to prevent "too_many_pings" warnings

**Find:** (around line 50-60, in ServiceConfig dataclass)
```python
keepalive_time_ms: int = 10000  # 10 seconds
```

**Replace with:**
```python
keepalive_time_ms: int = 20000  # 20 seconds (or 30000 for 30s)
```

**Alternative:** Update in `fastapi_app.py` where ServiceConfig is created:

**Find:** (around line 79-101)
```python
service_configs = {
    ServiceType.STT: ServiceConfig(
        host="stt-engine",
        port=50051,
        pool_size=3,
        max_retries=3,
        timeout=30.0
    ),
    # ... etc
}
```

**Replace with:**
```python
service_configs = {
    ServiceType.STT: ServiceConfig(
        host="stt-engine",
        port=50051,
        pool_size=3,
        max_retries=3,
        timeout=30.0,
        keepalive_time_ms=20000  # Add this
    ),
    ServiceType.NLP: ServiceConfig(
        host="nlp-service",
        port=50052,
        pool_size=2,
        max_retries=3,
        timeout=30.0,
        keepalive_time_ms=20000  # Add this
    ),
    ServiceType.SUMMARY: ServiceConfig(
        host="summary-service",
        port=50053,
        pool_size=2,
        max_retries=3,
        timeout=30.0,
        keepalive_time_ms=20000  # Add this
    ),
}
```

## Rebuild Commands

```bash
# Navigate to project directory
cd /home/frisco/projects/RTSTT

# Stop backend container
docker-compose stop backend

# Rebuild backend with no cache (ensures fresh build)
docker-compose build --no-cache backend

# Start backend container
docker-compose up -d backend

# Follow logs to verify startup
docker-compose logs -f backend
```

## Post-Rebuild Validation

### 1. Verify Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```
**Expected:** Prometheus metrics in text format (not 404)

### 2. Check Prometheus Targets
```bash
curl -s "http://localhost:9090/api/v1/targets" | python3 -c "
import json, sys
data = json.load(sys.stdin)
targets = data.get('data', {}).get('activeTargets', [])
for t in targets:
    job = t.get('labels', {}).get('job', 'unknown')
    health = t.get('health', 'unknown')
    state = '✅' if health == 'up' else '❌'
    print(f'{state} {job}: {health}')
"
```
**Expected:** Backend should show as "up"

### 3. Check for gRPC Warnings
```bash
docker-compose logs --tail=50 backend | grep -i "too_many_pings"
```
**Expected:** No results (if keepalive was adjusted)

### 4. Test Health Endpoint Still Works
```bash
curl http://localhost:8000/health | python3 -m json.tool
```
**Expected:** 200 OK with health status

### 5. Verify Container Health
```bash
docker-compose ps backend
```
**Expected:** Status shows "Up (healthy)"

## Success Criteria

After rebuild, all of these should be true:

- [ ] Backend container rebuilt successfully
- [ ] Backend container is running and healthy
- [ ] /health endpoint still working
- [ ] /metrics endpoint returns Prometheus metrics (200 response)
- [ ] Prometheus shows backend target as "up"
- [ ] No "too_many_pings" errors in backend logs
- [ ] All existing functionality still works
- [ ] Grafana can query backend metrics from Prometheus

## Rollback Plan

If rebuild fails:

```bash
# Stop and remove failed container
docker-compose stop backend
docker-compose rm -f backend

# Revert code changes
git checkout src/agents/orchestrator/fastapi_app.py
git checkout requirements.txt
# (only if modified) git checkout src/shared/protocols/grpc_pool.py

# Rebuild with old code
docker-compose build backend
docker-compose up -d backend

# Verify rollback
curl http://localhost:8000/health
```

## Additional Considerations

### Optional: Add Metrics to gRPC Services

If you want metrics from STT, NLP, and Summary services:

1. Add `prometheus-client` to their requirements
2. Add gRPC interceptors for metrics collection
3. Expose /metrics endpoint on a separate port (e.g., 9090)
4. Update Prometheus config to scrape those endpoints

**Note:** This is optional and not required for basic monitoring.

### Grafana Dashboard Creation

After metrics are flowing:

1. Access Grafana at http://localhost:3001
2. Login: admin/admin
3. Create new dashboard
4. Add panels querying backend metrics
5. Example queries:
   - `rate(http_requests_total[5m])` - Request rate
   - `histogram_quantile(0.95, http_request_duration_seconds)` - 95th percentile latency
   - `websocket_connections_active` - Active WebSocket connections

## Questions?

Refer to:
- Full test report: `/home/frisco/projects/RTSTT/system-test-report.txt`
- Test summary: `/home/frisco/projects/RTSTT/TESTING-SUMMARY.md`
- Prometheus docs: https://prometheus.io/docs/
- prometheus-client docs: https://github.com/prometheus/client_python

---

**Ready to proceed with backend rebuild when you are!**
