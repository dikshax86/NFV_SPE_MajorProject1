# NFV (Network Function Virtualization) - SPE Major Project

This project simulates **virtualized network functions** — a firewall, a switch, and a traffic monitor — deployed as microservices with a full CI/CD pipeline, container orchestration, monitoring, and centralized logging.

---

## Architecture Overview

```
                    +-------------+
                    |   Jenkins   |  <- CI/CD: Build, Push, Deploy
                    +------+------+
                           |
                    +------v------+
                    |  DockerHub  |  <- Image Registry (dknights/)
                    +------+------+
                           |
              +------------v----------------+
              |     Minikube (Kubernetes)    |
              |      namespace: nfv-system   |
              |                              |
  Ingress --> |  +--------+                  |
  (nfv.local) |  | Switch | <-- Entry point  |
              |  +---+--+-+                  |
              |      |  |                    |
              |      v  v                    |
              | +--------+  +---------+      |
              | |Firewall|  | Monitor |      |
              | +---+----+  +----+----+      |
              |     |            |           |
              |     v            v           |
              | +----------+ +-----------+   |
              | |Prometheus| |Elasticsearch|  |
              | +----+-----+ +-----+-----+   |
              |      v             v         |
              | +---------+  +--------+      |
              | | Grafana |  | Kibana |      |
              | +---------+  +--------+      |
              +------------------------------+
```

---

## Microservices (Application Code)

### 1. Switch Service (`switch-service/app.py`) - Port 5001

**Role:** The **entry point / router** of the network. All traffic enters here.

**What it does:**
- Receives incoming requests at `/route`
- Forwards every request to the **Firewall** for security checking
- Simultaneously sends the request to the **Monitor** for logging
- Returns the firewall's decision (allowed/blocked) to the caller

**Analogy:** Like a network switch that routes packets to the appropriate destination.

---

### 2. Firewall Service (`firewall-service/app.py`) - Port 5000

**Role:** The **security layer** that inspects and filters traffic.

**What it does:**
- Receives requests from the Switch
- Checks the source IP against a blocklist (`192.168.1.10`, `10.0.0.1`)
- Scans request content for malicious keywords (`DROP`, `malicious`, `attack`)
- Returns `403 Blocked` or `200 Allowed`
- Exposes Prometheus metrics at `/metrics` (counts allowed vs blocked requests)

**Analogy:** A network firewall that inspects packets and drops malicious ones.

---

### 3. Monitor Service (`monitor-service/app.py`) - Port 5002

**Role:** The **logging/observability layer** that records all traffic.

**What it does:**
- Receives every request from the Switch (regardless of firewall decision)
- Logs each request with IP, payload, and timestamp
- Stores logs locally in memory AND pushes them to **Elasticsearch**
- Exposes `/logs` endpoint to view recent logs

**Analogy:** A network tap / traffic analyzer that records everything for auditing.

---

## Containerization

### Dockerfiles (one per service)

Each service has a `Dockerfile` that:
- Uses a Python base image
- Installs dependencies from `requirements.txt`
- Copies the Flask app
- Exposes the relevant port
- Runs the app

### docker-compose.yml

For **local development/testing** without Kubernetes. Spins up:
- All 3 microservices
- Elasticsearch (for log storage)
- Kibana (for log visualization)

Run locally with: `docker-compose up`

---

## CI/CD Pipeline

### Jenkinsfile

Automates the entire build-to-deploy flow:

| Stage | What it does |
|-------|-------------|
| **Checkout** | Clones the GitHub repo (`dikshax86/NFV_SPE_MajorProject1`) |
| **Build Images** | Builds Docker images for all 3 services |
| **Login to DockerHub** | Authenticates using Jenkins credential `DockerHubCred` |
| **Push Images** | Pushes `dknights/firewall:v1`, `dknights/switch:v1`, `dknights/monitor:v1` to DockerHub |
| **Deploy to Kubernetes** | Runs `deploy.sh` to apply all K8s manifests to Minikube |

---

## Kubernetes Deployment (k8s/ directory)

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates the `nfv-system` namespace |
| `firewall-deployment.yaml` | Deploys firewall pod + ClusterIP service on port 5000 |
| `switch-deployment.yaml` | Deploys switch pod + ClusterIP service on port 5001 |
| `monitor-deployment.yaml` | Deploys monitor pod + ClusterIP service on port 5002 |
| `ingress.yaml` | Exposes Switch externally via hostname `nfv.local` |
| `storage.yaml` | PersistentVolume (1Gi) for Elasticsearch data |
| `prometheus-config.yaml` | ConfigMap defining Prometheus scrape targets |
| `prometheus.yaml` | Deploys Prometheus server on port 9090 |
| `grafana.yaml` | Deploys Grafana dashboard on port 3000 (NodePort) |
| `elasticsearch.yaml` | Deploys Elasticsearch 8.13.0 on port 9200 |
| `kibana.yaml` | Deploys Kibana 8.13.0 on NodePort 30602 |

---

## Monitoring Stack (Prometheus + Grafana)

- **Prometheus** scrapes the Firewall service every 5 seconds at `firewall:5000/metrics`
- Collects `allowed_requests_total` and `blocked_requests_total` counters
- **Grafana** connects to Prometheus as a data source to visualize firewall metrics

---

## Logging Stack (ELK)

- **Elasticsearch** stores all traffic logs sent by the Monitor service
- Uses a PersistentVolume for data durability across pod restarts
- **Kibana** provides a web UI to search and visualize logs

---

## Deploy Script (`deploy.sh`)

Applies all K8s manifests in the correct order:
1. Namespace
2. Storage (PV/PVC)
3. Prometheus config + deployment
4. Grafana
5. Elasticsearch + Kibana
6. Application services (firewall, monitor, switch)
7. Ingress
8. Restarts deployments to pull latest images

---

## Request Flow (End to End)

```
User sends POST to nfv.local/route
       |
       v
   [Ingress] -> routes to Switch:5001
       |
       v
   [Switch] --- sends to --> [Firewall:5000/check]
       |                            |
       |                     Checks IP + content
       |                            |
       |                     Returns: allowed/blocked
       |
       |--- sends to --> [Monitor:5002/log]
       |                        |
       |                  Logs to Elasticsearch
       |
       v
   Returns firewall decision to user
```

---

## How to Test

```bash
# Allowed request
curl -X POST http://nfv.local/route \
  -H "Content-Type: application/json" \
  -d '{"message": "hello world"}'
# Response: {"status": "allowed"}

# Blocked request (malicious keyword)
curl -X POST http://nfv.local/route \
  -H "Content-Type: application/json" \
  -d '{"message": "malicious attack"}'
# Response: {"status": "blocked", "reason": "malicious content"}

# Blocked request (blocked IP)
curl -X POST http://nfv.local/route \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 192.168.1.10" \
  -d '{"message": "hello"}'
# Response: {"status": "blocked", "reason": "IP blocked"}
```

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Application | Python, Flask |
| Containerization | Docker |
| Orchestration | Kubernetes (Minikube) |
| CI/CD | Jenkins (Pipeline) |
| Image Registry | DockerHub (`dknights/`) |
| Monitoring | Prometheus + Grafana |
| Logging | Elasticsearch + Kibana |
| Ingress | NGINX Ingress Controller |
| Version Control | Git + GitHub |

---

## Prerequisites for Local Setup

1. Docker installed and running
2. Minikube installed and started (`minikube start`)
3. Minikube ingress addon enabled (`minikube addons enable ingress`)
4. Jenkins installed with `DockerHubCred` credentials configured
5. Jenkins user has kubectl access to Minikube
6. `/etc/hosts` entry: `<minikube-ip> nfv.local`
