# Backend Rebuild - Quick Reference

## Quick Verification Commands

### Check Backend Health
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### View Metrics
```bash
curl http://localhost:8000/metrics | less
```

### Check Prometheus Targets
```bash
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -A10 backend
```

### Monitor Backend Logs
```bash
docker-compose logs -f backend
```

### Check Container Status
```bash
docker-compose ps backend
```

### View Custom Metrics
```bash
curl -s http://localhost:8000/metrics | grep -E "transcription|grpc|websocket"
```

### Query Metrics from Prometheus
```bash
# HTTP requests
curl -s "http://localhost:9090/api/v1/query?query=http_requests_total{job='backend'}"

# WebSocket connections
curl -s "http://localhost:9090/api/v1/query?query=websocket_connections_active"

# Process memory
curl -s "http://localhost:9090/api/v1/query?query=process_resident_memory_bytes{job='backend'}"
```

## Access URLs

- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Metrics Endpoint:** http://localhost:8000/metrics
- **Prometheus UI:** http://localhost:9090
- **Grafana:** http://localhost:3001 (admin/admin)

## Reports Location

- **Detailed Report:** `/home/frisco/projects/RTSTT/backend-rebuild-report.txt`
- **Summary:** `/home/frisco/projects/RTSTT/BACKEND-REBUILD-SUMMARY.md`
- **Checklist:** `/home/frisco/projects/RTSTT/BACKEND-REBUILD-CHECKLIST.md`

## If You Need to Rebuild Again

```bash
cd /home/frisco/projects/RTSTT
docker-compose stop backend
docker-compose rm -f backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

## Troubleshooting

### Metrics endpoint returns 404
Check environment variable:
```bash
docker-compose config | grep -A1 backend | grep ENABLE_METRICS
```

### Prometheus not scraping
Check target status:
```bash
curl http://localhost:9090/targets
```

### Container won't start
Check logs:
```bash
docker-compose logs backend --tail=100
```

---
Last updated: 2025-11-24
