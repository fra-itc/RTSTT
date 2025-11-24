# Monitoring Quick Start Guide

## Quick Access

### URLs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Metrics**: http://localhost:8000/metrics

## Start Monitoring

```bash
cd /home/frisco/projects/RTSTT
docker-compose up -d prometheus grafana redis-exporter
```

## Check Status

```bash
# All monitoring services
docker-compose ps prometheus grafana redis-exporter

# Prometheus health
curl http://localhost:9090/-/healthy

# Grafana health
curl http://localhost:3001/api/health

# Backend metrics (after rebuild)
curl http://localhost:8000/metrics
```

## View Dashboard

1. Open http://localhost:3001
2. Login: admin/admin
3. Navigate to "RTSTT Integration Platform - Production Monitoring"

## Rebuild Backend (if needed)

```bash
docker-compose build backend
docker-compose up -d backend
```

## Common Prometheus Queries

```promql
# Request rate
rate(http_requests_total[5m])

# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])

# Active WebSocket connections
websocket_connections_active

# Redis status
redis_up
```

## Troubleshooting

```bash
# View logs
docker-compose logs prometheus
docker-compose logs grafana
docker-compose logs backend

# Restart services
docker-compose restart prometheus grafana

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Full Documentation

See `/home/frisco/projects/RTSTT/docs/MONITORING_GUIDE.md` for complete guide.
