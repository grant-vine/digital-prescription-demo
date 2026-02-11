## Title
Production Monitoring and Observability

## Description
Implement comprehensive monitoring, logging, and alerting to ensure the digital prescription system operates reliably in production and issues are detected and resolved quickly.

## Context
Production systems require visibility into performance, errors, and user behavior. This story establishes the observability foundation for operations teams.

## Acceptance Criteria

### Metrics Collection (Prometheus)
- [ ] Application metrics exposed via /metrics endpoint
- [ ] Request rate, latency, error rate (RED metrics)
- [ ] Business metrics:
  - Prescriptions created per hour
  - Verification success/failure rate
  - Average time doctor→patient→pharmacist
  - Active users per role
- [ ] Infrastructure metrics:
  - CPU, memory, disk usage
  - Database connections
  - API response times
  - ACA-Py agent health
- [ ] Custom metrics for SSI operations:
  - DID operations count
  - VC issuance time
  - Verification time
  - Connection count

### Dashboards (Grafana)
- [ ] System Overview Dashboard
  - Health status of all services
  - Request rates and latencies
  - Error rates
  - Resource utilization
- [ ] Business Metrics Dashboard
  - Prescription volume
  - User activity by role
  - Geographic distribution
  - Peak usage times
- [ ] SSI Operations Dashboard
  - DID operations
  - Credential lifecycle
  - Verification statistics
  - Connection health
- [ ] Mobile App Dashboard
  - Active sessions
  - Crash rates
  - API latency from mobile
  - Feature usage
- [ ] Alerting rules configured

### Logging (Loki / ELK)
- [ ] Structured logging (JSON format)
- [ ] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [ ] Correlation IDs for request tracing
- [ ] Sensitive data redaction
- [ ] Log retention policy (30-90 days)
- [ ] Searchable log aggregation
- [ ] Error log alerting

### Distributed Tracing (Jaeger)
- [ ] End-to-end request tracing
- [ ] Trace across microservices
- [ ] Database query tracing
- [ ] External API call tracing
- [ ] ACA-Py operation tracing
- [ ] Performance bottleneck identification

### Alerting (PagerDuty / Opsgenie)
- [ ] Critical alerts (page on-call):
  - Service down
  - Database unreachable
  - High error rate (>5%)
  - ACA-Py agent failures
- [ ] Warning alerts (Slack/email):
  - High latency (>2s)
  - Disk space >80%
  - Memory usage >85%
  - Unusual error patterns
- [ ] Alert routing and escalation
- [ ] Runbook links in alerts

### Uptime Monitoring
- [ ] External health checks (Pingdom / UptimeRobot)
- [ ] Synthetic monitoring (test prescription flow every 5 minutes)
- [ ] Geographic monitoring (multiple locations)
- [ ] SSL certificate expiry alerts
- [ ] DNS monitoring

### Mobile App Monitoring
- [ ] Crash reporting (Sentry / Firebase Crashlytics)
- [ ] Performance monitoring (Firebase Performance)
- [ ] ANR (Application Not Responding) detection
- [ ] Network failure tracking
- [ ] User session tracking

### Security Monitoring
- [ ] Failed authentication attempts
- [ ] Suspicious activity patterns
- [ ] Rate limit violations
- [ ] Unusual data access patterns
- [ ] Integration with SIEM (future)

## Technical Implementation

### Prometheus Metrics Example
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'prescription_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'prescription_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Business metrics
prescriptions_created = Counter(
    'prescriptions_created_total',
    'Total prescriptions created',
    ['doctor_id']
)

verifications = Counter(
    'prescription_verifications_total',
    'Total verifications',
    ['result']
)

# Infrastructure
active_connections = Gauge(
    'acapy_active_connections',
    'Active ACA-Py connections'
)
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Usage
logger.info(
    "prescription_created",
    prescription_id="RX-001",
    doctor_did="did:cheqd:...",
    patient_did="did:cheqd:...",
    correlation_id="uuid-123",
    duration_ms=245
)
```

### Distributed Tracing
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def create_prescription(data):
    with tracer.start_as_current_span("create_prescription") as span:
        span.set_attribute("prescription.id", data['id'])
        span.set_attribute("doctor.did", data['doctor_did'])
        
        # Database call
        with tracer.start_span("db_insert"):
            await db.prescriptions.insert(data)
        
        # ACA-Py call
        with tracer.start_span("acapy_issue_credential"):
            await acapy.issue_credential(data)
        
        return prescription
```

## Dashboard Examples

### System Health
```
┌────────────────────────────────────────────────────────────┐
│ SYSTEM HEALTH                                              │
├────────────────────────────────────────────────────────────┤
│ ✅ API: Healthy (3/3 pods)                                 │
│ ✅ ACA-Py: Healthy (3/3 pods)                              │
│ ✅ PostgreSQL: Healthy (2/2 pods)                          │
│ ✅ Redis: Healthy (3/3 pods)                               │
├────────────────────────────────────────────────────────────┤
│ REQUESTS/SEC: 45    ERROR RATE: 0.2%    LATENCY: 120ms     │
└────────────────────────────────────────────────────────────┘
```

### Business Metrics
```
┌────────────────────────────────────────────────────────────┐
│ TODAY'S ACTIVITY                                           │
├────────────────────────────────────────────────────────────┤
│ Prescriptions Created: 127                                 │
│ Verifications: 89                                          │
│ Active Doctors: 23                                         │
│ Active Patients: 156                                       │
│ Avg. Prescription Flow: 4.2 hours                          │
└────────────────────────────────────────────────────────────┘
```

## Alerting Rules

```yaml
# prometheus-alerts.yaml
groups:
  - name: prescription-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(prescription_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"
          
      - alert: ServiceDown
        expr: up{job="prescription-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Prescription API is down"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(prescription_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses"
```

## Estimation
- **Story Points**: 8
- **Time Estimate**: 4-5 days
- **Dependencies**: US-024 (Kubernetes Deployment)

## Tools Stack

| Purpose | Tool | Alternative |
|---------|------|-------------|
| Metrics | Prometheus | Datadog, New Relic |
| Dashboards | Grafana | Datadog, New Relic |
| Logging | Loki | ELK Stack, Splunk |
| Tracing | Jaeger | Zipkin, Tempo |
| Alerting | PagerDuty | Opsgenie, VictorOps |
| Uptime | Pingdom | UptimeRobot, Datadog |
| Errors | Sentry | Rollbar, Bugsnag |
| Mobile | Firebase | Sentry, Crashlytics |

## Cost

**Open Source Stack (Self-hosted):**
- Infrastructure: ~$100-200/month
- Storage: ~$50-100/month
- Total: ~$150-300/month

**SaaS Options:**
- Datadog: ~$70/host/month
- New Relic: ~$99/host/month
- Splunk: ~$180/GB/month

## Related Stories
- Depends on: US-024 (Kubernetes Deployment)
- Related: US-026 (Security Hardening)
