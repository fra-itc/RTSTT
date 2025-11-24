# RTSTT Monitoring Guide

## Overview

This guide explains how to use the observability stack (Prometheus + Grafana) to monitor the RTSTT (Real-Time Speech-to-Text) integration platform in production and development environments.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Accessing the Monitoring Stack](#accessing-the-monitoring-stack)
3. [Grafana Dashboards](#grafana-dashboards)
4. [Prometheus Metrics](#prometheus-metrics)
5. [Common Use Cases](#common-use-cases)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Queries](#advanced-queries)

---

## Architecture Overview

The RTSTT observability stack consists of:

- **Prometheus**: Time-series database for metrics collection
- **Grafana**: Visualization and dashboarding platform
- **Redis Exporter**: Exports Redis metrics to Prometheus
- **Backend Instrumentation**: Custom metrics from FastAPI application

### Component Ports

| Service | Port | URL |
|---------|------|-----|
| Grafana | 3001 | http://localhost:3001 |
| Prometheus | 9090 | http://localhost:9090 |
| Backend API | 8000 | http://localhost:8000 |
| Backend Metrics | 8000 | http://localhost:8000/metrics |
| Redis Exporter | 9121 | http://localhost:9121/metrics |

---

## Accessing the Monitoring Stack

### Starting the Services

```bash
# Start all services (including monitoring)
cd /home/frisco/projects/RTSTT
docker-compose up -d

# Start only monitoring services
docker-compose up -d prometheus grafana redis-exporter

# Check service status
docker-compose ps
```

### Accessing Grafana

1. Open your browser and navigate to: **http://localhost:3001**
2. Login with default credentials:
   - **Username**: `admin`
   - **Password**: `admin`
3. You'll be prompted to change the password (recommended in production)

### Accessing Prometheus

1. Open your browser and navigate to: **http://localhost:9090**
2. No authentication required (add in production!)
3. Go to **Status > Targets** to verify all services are being scraped

---

## Grafana Dashboards

### Pre-configured Dashboards

The system comes with a comprehensive dashboard: **"RTSTT Integration Platform - Production Monitoring"**

#### Dashboard Panels

1. **HTTP Request Latency (p95/p99)**
   - Shows 95th and 99th percentile latency for all HTTP endpoints
   - Useful for identifying slow endpoints

2. **HTTP Request Throughput**
   - Requests per second by endpoint
   - Helps identify traffic patterns

3. **HTTP Error Rate (5xx)**
   - Percentage of server errors
   - Gauge visualization with thresholds (green < 1%, yellow < 5%, red >= 5%)

4. **HTTP Requests by Status Code**
   - Stacked area chart showing all status codes
   - Useful for spotting error patterns

5. **Active WebSocket Connections**
   - Real-time count of connected clients
   - Critical for capacity planning

6. **WebSocket Message Rate**
   - Messages sent/received per second
   - Broken down by message type

7. **Redis Pub/Sub Message Rate**
   - Redis channel activity
   - Shows internal message passing

8. **Redis Operation Latency (p95)**
   - Database operation performance
   - Helps identify Redis bottlenecks

9. **gRPC Request Rate**
   - Requests to STT, NLP, and Summary services
   - Broken down by service and method

10. **gRPC Request Latency (p95)**
    - 95th percentile latency for gRPC calls
    - Critical for pipeline performance monitoring

11. **gRPC Error Rate**
    - Percentage of failed gRPC requests
    - Gauge with color-coded thresholds

12. **Active Transcription Sessions**
    - Number of ongoing transcriptions
    - Useful for load monitoring

13. **Redis Connected Clients**
    - Pie chart of Redis client connections
    - Helps identify connection leaks

14. **Redis Health Status**
    - Binary indicator (1 = healthy, 0 = down)
    - Quick visual health check

### Dashboard Features

- **Auto-refresh**: Updates every 10 seconds
- **Time range**: Default last 1 hour (customizable)
- **Dark mode**: Enabled by default
- **Interactive**: Click on legend items to show/hide series

---

## Prometheus Metrics

### Backend Metrics

#### HTTP Metrics (from prometheus-fastapi-instrumentator)

```promql
# Request count by endpoint
http_requests_total{endpoint="/ws"}

# Request duration histogram
http_request_duration_seconds_bucket{endpoint="/health"}

# In-progress requests
http_requests_inprogress{endpoint="/ws"}
```

#### Custom Application Metrics

```promql
# Transcription requests by language and status
transcription_requests_total{language="en", status="success"}

# Transcription latency by service (STT, NLP, Summary)
transcription_latency_seconds{service="stt"}

# Active WebSocket connections
websocket_connections_active{endpoint="/ws"}

# WebSocket message counters
websocket_messages_sent_total{endpoint="/ws", message_type="status"}
websocket_messages_received_total{endpoint="/ws", message_type="text"}

# Active transcription sessions
transcription_sessions_active

# gRPC metrics
grpc_requests_total{service="stt-engine", method="Transcribe", status="success"}
grpc_request_duration_seconds_bucket{service="nlp-service", method="Analyze"}
```

#### Redis Metrics (from redis-exporter)

```promql
# Redis is up
redis_up

# Connected clients
redis_connected_clients

# Commands processed
redis_commands_processed_total

# Memory usage
redis_used_memory_bytes

# Pub/Sub channels
redis_pubsub_channels
redis_pubsub_patterns
```

---

## Common Use Cases

### 1. Checking System Health

**Grafana**: Open the main dashboard and check:
- Error rate gauges (should be green)
- Redis health status (should be 1)
- Active connections (should match expected load)

**Prometheus**: Navigate to **Status > Targets**
- All targets should be "UP"
- If a target is down, check the service logs

### 2. Investigating High Latency

**In Grafana**:
1. Check the "HTTP Request Latency (p95/p99)" panel
2. Identify which endpoint has high latency
3. Check "gRPC Request Latency" to see if the issue is in the pipeline
4. Review "Redis Operation Latency" for database bottlenecks

**In Prometheus**:
```promql
# Find slowest endpoints
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])))

# Check specific endpoint latency over time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint="/ws"}[5m]))
```

### 3. Monitoring WebSocket Performance

**Key Metrics**:
- Active connections: `websocket_connections_active`
- Message rate: `rate(websocket_messages_sent_total[5m])`
- Connection errors: Check HTTP 4xx/5xx on `/ws` endpoint

**Alerting Thresholds** (recommended):
- Max connections > 1000: Scale up
- Message rate > 10,000/sec: Performance review needed
- Error rate > 5%: Investigate immediately

### 4. Tracking gRPC Service Performance

**Useful Queries**:
```promql
# STT service request rate
sum(rate(grpc_requests_total{service="stt-engine"}[5m]))

# NLP service p99 latency
histogram_quantile(0.99, rate(grpc_request_duration_seconds_bucket{service="nlp-service"}[5m]))

# Summary service error rate
sum(rate(grpc_requests_total{service="summary-service", status="error"}[5m])) /
sum(rate(grpc_requests_total{service="summary-service"}[5m]))
```

### 5. Capacity Planning

**Metrics to Monitor**:
1. Peak active connections
2. Average message throughput
3. CPU/Memory usage (requires cAdvisor - optional)
4. Request latency trends

**Example Query**:
```promql
# Peak connections in last 24h
max_over_time(websocket_connections_active[24h])

# Average throughput
avg_over_time(rate(http_requests_total[5m])[24h:5m])
```

---

## Troubleshooting

### Grafana shows "No Data"

**Possible causes**:
1. Prometheus is not running
2. Services are not exposing metrics
3. Scrape interval hasn't elapsed yet

**Solutions**:
```bash
# Check Prometheus is running
docker-compose ps prometheus

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check backend metrics endpoint
curl http://localhost:8000/metrics

# Restart Prometheus
docker-compose restart prometheus
```

### Prometheus shows target as "DOWN"

**For backend target**:
```bash
# Check backend is running
docker-compose ps backend

# Check backend health
curl http://localhost:8000/health

# View backend logs
docker-compose logs backend --tail=50
```

**For gRPC services**:
```bash
# Check service is running
docker-compose ps stt-engine nlp-service summary-service

# View service logs
docker-compose logs stt-engine --tail=50
```

### Metrics not updating

1. **Check scrape interval**: Prometheus scrapes every 15s by default
2. **Verify traffic**: Metrics only update when there's activity
3. **Check time range**: Ensure Grafana time range includes recent data

### Dashboard shows wrong data

1. **Verify Prometheus datasource**:
   - Grafana > Configuration > Data Sources
   - Test the connection

2. **Check dashboard queries**:
   - Edit panel
   - Verify PromQL syntax
   - Use Prometheus UI to test queries

---

## Advanced Queries

### Finding the Top Error Endpoints

```promql
topk(5,
  sum by (endpoint) (rate(http_requests_total{status_code=~"5.."}[5m]))
)
```

### Calculating Overall System Success Rate

```promql
(
  sum(rate(http_requests_total{status_code!~"5.."}[5m])) /
  sum(rate(http_requests_total[5m]))
) * 100
```

### Detecting WebSocket Connection Spikes

```promql
# Rate of change
deriv(websocket_connections_active[5m])

# Connections increasing > 10/min
increase(websocket_connections_active[1m]) > 10
```

### Analyzing gRPC Performance by Method

```promql
# Latency breakdown by service and method
histogram_quantile(0.95,
  sum by (le, service, method) (
    rate(grpc_request_duration_seconds_bucket[5m])
  )
)
```

### Redis Memory Usage Trend

```promql
# Memory usage change over 1h
delta(redis_used_memory_bytes[1h])

# Predicted memory in 24h (linear extrapolation)
predict_linear(redis_used_memory_bytes[1h], 86400)
```

---

## Best Practices

### 1. Set Up Alerts

Create alert rules in Prometheus for:
- Error rate > 5%
- Latency p95 > 5 seconds
- Redis down
- gRPC service errors > 1%

### 2. Regular Health Checks

- Review dashboards daily
- Check for anomalies in traffic patterns
- Monitor long-term trends

### 3. Dashboard Customization

- Create custom dashboards for specific services
- Add annotations for deployments
- Use variables for dynamic filtering

### 4. Data Retention

- Prometheus retains 30 days by default
- For longer retention, set up remote storage
- Export critical metrics for archival

### 5. Security

In production:
- Change default Grafana password
- Enable Prometheus authentication
- Use HTTPS for all services
- Restrict network access

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)

---

## Support

For issues or questions:
1. Check service logs: `docker-compose logs <service-name>`
2. Review this guide
3. Consult Prometheus/Grafana documentation
4. Contact the development team

---

**Last Updated**: 2025-11-24
**Version**: 1.0.0
**Maintainer**: RTSTT Development Team
