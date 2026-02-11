## Title
Production Kubernetes Deployment

## Description
Deploy the digital prescription system to Kubernetes cluster with proper scaling, monitoring, security, and reliability for production use.

## Context
Current MVP runs on Docker Compose locally. For production, we need cloud deployment with proper orchestration, high availability, and operational tooling.

## Acceptance Criteria

### Kubernetes Manifests
- [ ] Deployment manifests for all services
- [ ] Service definitions (ClusterIP, LoadBalancer)
- [ ] ConfigMaps for configuration
- [ ] Secrets for sensitive data
- [ ] Persistent Volume Claims for databases
- [ ] Horizontal Pod Autoscaler (HPA)
- [ ] Pod Disruption Budgets

### Helm Charts
- [ ] Helm chart for backend API
- [ ] Helm chart for mobile app (if server-side rendering)
- [ ] Helm chart for ACA-Py agents
- [ ] Helm chart for databases (PostgreSQL, Redis)
- [ ] Values files for dev/staging/prod
- [ ] Chart dependencies managed

### Networking
- [ ] Ingress controller (nginx or traefik)
- [ ] SSL/TLS certificates (cert-manager + Let's Encrypt)
- [ ] Domain configuration
- [ ] CORS configuration
- [ ] Rate limiting at ingress
- [ ] WebSocket support (for real-time features)

### Security
- [ ] Network policies
- [ ] Pod security policies / OPA Gatekeeper
- [ ] Service mesh (Istio/Linkerd) optional
- [ ] Secrets encryption (Sealed Secrets or external KMS)
- [ ] RBAC configuration
- [ ] Security scanning (Trivy, Clair)

### Observability
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards
- [ ] Loki for log aggregation
- [ ] Distributed tracing (Jaeger)
- [ ] Uptime monitoring
- [ ] Alerting rules (PagerDuty/Opsgenie integration)

### Database
- [ ] PostgreSQL operator or Helm chart
- [ ] Automated backups
- [ ] Point-in-time recovery
- [ ] Connection pooling (PgBouncer)
- [ ] Read replicas for scaling

### ACA-Py Deployment
- [ ] ACA-Py as StatefulSet (for wallet persistence)
- [ ] Multi-tenant configuration
- [ ] Ledger connection (indy-node)
- [ ] Wallet storage (PostgreSQL)
- [ ] Webhook integration

### CI/CD Integration
- [ ] GitOps with ArgoCD or Flux
- [ ] Automated deployments
- [ ] Canary deployments
- [ ] Rollback capability
- [ ] Image scanning in pipeline

### Resource Management
- [ ] Resource requests and limits
- [ ] Quality of Service classes
- [ ] Node affinity/anti-affinity
- [ ] Taints and tolerations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐                                        │
│  │   Ingress       │  ← SSL termination, rate limiting     │
│  │   Controller    │                                        │
│  └────────┬────────┘                                        │
│           │                                                  │
│  ┌────────▼────────┐                                        │
│  │   API Gateway   │  ← Authentication, routing            │
│  └────────┬────────┘                                        │
│           │                                                  │
│  ┌────────▼────────────────────────────────────────────┐   │
│  │              SERVICES (Microservices)                │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │   │
│  │  │  Auth        │ │ Prescription │ │ Verification │  │   │
│  │  │  Service     │ │  Service     │ │   Service    │  │   │
│  │  │  (3 replicas)│ │  (3 replicas)│ │  (3 replicas)│  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘  │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  ACA-Py Agents (StatefulSet)                            ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                   ││
│  │  │ Agent 1 │ │ Agent 2 │ │ Agent 3 │                   ││
│  │  │(Doctor) │ │(Patient)│ │(Pharmacy│                   ││
│  │  └─────────┘ └─────────┘ └─────────┘                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  DATA STORES                                            ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    ││
│  │  │ PostgreSQL   │ │    Redis     │ │   MinIO      │    ││
│  │  │ (HA cluster) │ │   (cluster)  │ │  (S3-like)   │    ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Helm Chart Structure

```
helm/
├── digital-prescription/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── hpa.yaml
│       ├── pdb.yaml
│       ├── configmap.yaml
│       └── secrets.yaml
└── acapy/
    └── ...
```

## Deployment Commands

```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install dependencies
helm install postgres bitnami/postgresql-ha -f values-postgres.yaml
helm install redis bitnami/redis-cluster
helm install ingress ingress-nginx/ingress-nginx

# Install application
helm install digital-prescription ./helm/digital-prescription \
  -f values-prod.yaml \
  --namespace production \
  --create-namespace

# Upgrade
helm upgrade digital-prescription ./helm/digital-prescription \
  -f values-prod.yaml \
  --namespace production

# Rollback
helm rollback digital-prescription 3
```

## Monitoring Stack

```yaml
# prometheus-values.yaml
prometheus:
  prometheusSpec:
    retention: 30d
    resources:
      requests:
        memory: 2Gi
      limits:
        memory: 4Gi

grafana:
  enabled: true
  adminPassword: admin
  dashboards:
    default:
      digital-prescription:
        url: https://raw.githubusercontent.com/.../dashboard.json
```

## Resource Requirements

### Production Sizing (Initial)
```yaml
# Minimum viable production
backend:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

acapy:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi

postgresql:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
```

## Estimation
- **Story Points**: 13
- **Time Estimate**: 5-7 days
- **Dependencies**: All previous stories (this is deployment phase)

## Notes

### Cloud Provider Options
- **AWS**: EKS + ALB + RDS + S3
- **GCP**: GKE + Cloud Load Balancing + Cloud SQL + Cloud Storage
- **Azure**: AKS + Application Gateway + Azure SQL + Blob Storage

### On-Premises
- Vanilla Kubernetes (kubeadm, k3s, RKE2)
- OpenShift
- Rancher

### Cost Considerations
- Minimum 3 nodes for HA (~$200-500/month per cloud)
- Managed databases reduce ops burden but increase cost
- Start small, scale up

## Related Stories
- Depends on: All MVP and Enhanced stories
- Related: US-025 (Monitoring & Alerting), US-026 (Security Hardening)
