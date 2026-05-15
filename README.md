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

## What Each Component Does

### Application Microservices

| Service | Port | Role |
|---------|------|------|
| **Switch** | 5001 | Entry point. Routes all incoming traffic to Firewall and Monitor |
| **Firewall** | 5000 | Security layer. Checks IPs and content, blocks malicious traffic |
| **Monitor** | 5002 | Logging layer. Records all traffic and sends to Elasticsearch |

### Monitoring Stack (Metrics - "How much traffic?")

| Tool | Role |
|------|------|
| **Prometheus** | Scrapes firewall metrics every 5 seconds, stores time-series data |
| **Grafana** | Visualizes Prometheus data as dashboards (graphs, gauges, pie charts) |

### Logging Stack (Logs - "What was in the traffic?")

| Tool | Role |
|------|------|
| **Elasticsearch** | Stores full traffic logs (IP, payload, timestamp) as searchable documents |
| **Kibana** | Web UI to search, filter, and visualize logs stored in Elasticsearch |

### Key Difference: Prometheus vs Elasticsearch

```
Prometheus = NUMBERS (how many requests? how many blocked?)
    -> Grafana shows GRAPHS of those numbers over time

Elasticsearch = FULL LOGS (what IP? what data? what time?)
    -> Kibana lets you SEARCH through those logs
```

**Example:**
- Prometheus tells you: "There were 50 blocked requests in the last hour"
- Elasticsearch tells you: "Here are all 50 blocked requests — this IP sent this payload at this time"

---

## Project File Structure

```
NFV_Diksha/
├── Jenkinsfile                    # CI/CD pipeline definition
├── deploy.sh                      # K8s deployment script
├── docker-compose.yml             # Local development setup
├── post.json                      # Sample test payload
│
├── switch-service/                # Entry point microservice
│   ├── app.py                     # Flask app (routes traffic)
│   ├── Dockerfile                 # Container definition
│   └── requirements.txt           # Python dependencies
│
├── firewall-service/              # Security microservice
│   ├── app.py                     # Flask app (blocks/allows traffic)
│   ├── Dockerfile                 # Container definition
│   └── requirements.txt           # Python dependencies
│
├── monitor-service/               # Logging microservice
│   ├── app.py                     # Flask app (logs to Elasticsearch)
│   ├── Dockerfile                 # Container definition
│   └── requirements.txt           # Python dependencies
│
└── k8s/                           # Kubernetes manifests
    ├── namespace.yaml             # Creates nfv-system namespace
    ├── storage.yaml               # Persistent storage for Elasticsearch
    ├── firewall-deployment.yaml   # Firewall pod + service
    ├── switch-deployment.yaml     # Switch pod + service
    ├── monitor-deployment.yaml    # Monitor pod + service
    ├── ingress.yaml               # External access via nfv.local
    ├── prometheus-config.yaml     # Prometheus scrape configuration
    ├── prometheus.yaml            # Prometheus deployment
    ├── grafana.yaml               # Grafana deployment
    ├── elasticsearch.yaml         # Elasticsearch deployment
    └── kibana.yaml                # Kibana deployment
```

---

## Complete Setup Guide (Step by Step)

### Prerequisites

The following must be installed:
- Docker
- Minikube
- kubectl
- Jenkins
- Java (for Jenkins)

### Step 1: Start Minikube

```bash
minikube start
```

This starts a local single-node Kubernetes cluster.

### Step 2: Enable Ingress Addon

```bash
minikube addons enable ingress
```

This installs the NGINX Ingress Controller so external traffic can reach your services via `nfv.local`.

### Step 3: Add nfv.local to /etc/hosts

```bash
echo "$(minikube ip) nfv.local" | sudo tee -a /etc/hosts
```

This maps the hostname `nfv.local` to your Minikube cluster's IP address so your browser/curl can reach it.

### Step 4: Login to DockerHub

```bash
docker login -u dknights
```

Enter your DockerHub password when prompted. This allows Docker to push images.

### Step 5: Give Jenkins Access to Docker

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

This adds the `jenkins` user to the `docker` group so Jenkins can build and push images.

### Step 6: Give Jenkins Access to kubectl (Minikube)

```bash
# Copy kubeconfig
sudo mkdir -p /var/lib/jenkins/.kube
sudo cp ~/.kube/config /var/lib/jenkins/.kube/config
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube

# Copy minikube certificates
sudo mkdir -p /var/lib/jenkins/.minikube/profiles/minikube
sudo cp ~/.minikube/ca.crt /var/lib/jenkins/.minikube/ca.crt
sudo cp ~/.minikube/profiles/minikube/client.crt /var/lib/jenkins/.minikube/profiles/minikube/client.crt
sudo cp ~/.minikube/profiles/minikube/client.key /var/lib/jenkins/.minikube/profiles/minikube/client.key
sudo chown -R jenkins:jenkins /var/lib/jenkins/.minikube

# Fix paths in kubeconfig to point to Jenkins' copy
sudo sed -i "s|/home/$(whoami)/.minikube|/var/lib/jenkins/.minikube|g" /var/lib/jenkins/.kube/config
```

This gives Jenkins the ability to run `kubectl` commands against your Minikube cluster.

### Step 7: Verify Jenkins can access Kubernetes

```bash
sudo -u jenkins kubectl get nodes
```

Expected output:
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   ...   v1.35.1
```

### Step 8: Configure DockerHub Credentials in Jenkins UI

1. Open Jenkins: http://localhost:8080
2. Go to **Manage Jenkins** -> **Credentials** -> **System** -> **Global credentials**
3. Click **Add Credentials**
4. Fill in:
   - Kind: `Username with password`
   - Username: `dknights`
   - Password: Your DockerHub password or access token
   - ID: `DockerHubCred`
   - Description: `Docker Hub Credentials`
5. Click **Create**

### Step 9: Create Jenkins Pipeline Job

1. In Jenkins -> **New Item**
2. Name: `NFV` (or any name)
3. Type: **Pipeline**
4. Under **Pipeline** section:
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/dikshax86/NFV_SPE_MajorProject1.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
5. Click **Save**

### Step 10: Run the Pipeline

Click **Build Now** on the pipeline job.

The pipeline will:
1. **Checkout** - Clone code from GitHub
2. **Build Images** - Build Docker images for firewall, switch, monitor
3. **Login to DockerHub** - Authenticate with DockerHubCred
4. **Push Images** - Push dknights/firewall:v1, dknights/switch:v1, dknights/monitor:v1
5. **Deploy to Kubernetes** - Run deploy.sh which applies all K8s manifests

### Step 11: Verify Deployment

```bash
kubectl get all -n nfv-system
```

Expected: All pods should show `STATUS: Running`

---

## How to Test Each Component

### Test 1: Allowed Request (through Ingress)

```bash
curl -X POST http://nfv.local/route -H "Content-Type: application/json" -d '{"message": "hello world"}'
```

Expected response:
```json
{"status": "allowed"}
```

**Flow:** User -> Ingress -> Switch -> Firewall (checks, allows) + Monitor (logs it)

### Test 2: Blocked Request (Malicious Keyword)

```bash
curl -X POST http://nfv.local/route -H "Content-Type: application/json" -d '{"message": "malicious attack"}'
```

Expected response:
```json
{"status": "blocked", "reason": "malicious content"}
```

**Flow:** User -> Ingress -> Switch -> Firewall (detects "malicious", blocks) + Monitor (logs it)

### Test 3: Blocked Request (Blocked IP)

```bash
curl -X POST http://nfv.local/route -H "Content-Type: application/json" -H "X-Forwarded-For: 192.168.1.10" -d '{"message": "hello"}'
```

**Note:** IP blocking works inside the cluster. The ingress controller may override the X-Forwarded-For header externally.

### Test 4: Generate Bulk Traffic

```bash
# Send 10 allowed requests
for i in {1..10}; do curl -s -X POST http://nfv.local/route -H "Content-Type: application/json" -d '{"message": "hello"}'; echo; done

# Send 5 blocked requests
for i in {1..5}; do curl -s -X POST http://nfv.local/route -H "Content-Type: application/json" -d '{"message": "malicious attack"}'; echo; done
```

### Test 5: Check Monitor Logs (in-memory)

```bash
kubectl exec -n nfv-system deployment/monitor -- python -c "
import requests
r = requests.get('http://localhost:5002/logs')
print(r.json())
"
```

This shows all logged requests stored in the Monitor service's memory.

### Test 6: Check Elasticsearch (persistent logs)

```bash
kubectl exec -n nfv-system deployment/elasticsearch -- curl -s http://localhost:9200/logs/_search?pretty
```

This shows all logged requests stored permanently in Elasticsearch.

### Test 7: Check Prometheus Metrics

```bash
kubectl exec -n nfv-system deployment/prometheus -- wget -qO- "http://localhost:9090/api/v1/query?query=allowed_requests_total"
```

This shows the total count of allowed requests as tracked by Prometheus.

### Test 8: Check Firewall Metrics Endpoint Directly

```bash
kubectl exec -n nfv-system deployment/firewall -- curl -s http://localhost:5000/metrics
```

This shows the raw Prometheus metrics exposed by the firewall service.

---

## Accessing the UIs

### Grafana (Dashboards - Visual Monitoring)

```
URL: http://<minikube-ip>:32210
Login: admin / admin
```

**What it shows:** Real-time graphs of firewall traffic (allowed vs blocked over time)

**How to get the URL:**
```bash
echo "http://$(minikube ip):32210"
```

**Setting up Grafana:**
1. Login with admin/admin
2. Go to Connections -> Data sources -> Add data source
3. Select Prometheus
4. URL: `http://prometheus:9090`
5. Click Save & Test
6. Go to Dashboards -> New -> New Dashboard
7. Add Panel -> Select Prometheus data source
8. Metric: `allowed_requests_total` -> Run queries
9. Add Query B: `blocked_requests_total`
10. Click Apply, then Save

### Kibana (Log Search & Analysis)

```
URL: http://<minikube-ip>:30602
```

**What it shows:** Full searchable logs of all traffic that passed through the system

**How to get the URL:**
```bash
echo "http://$(minikube ip):30602"
```

**Setting up Kibana:**
1. Open Kibana URL in browser
2. Go to Management -> Stack Management -> Index Patterns (or Data Views)
3. Create index pattern: `logs*`
4. Time field: `timestamp`
5. Go to Discover (left sidebar) to search through logs
6. You can filter by IP, message content, time range, etc.

### Prometheus (Metric Queries - Debugging)

```bash
kubectl port-forward svc/prometheus 9090:9090 -n nfv-system
```

Then open: `http://localhost:9090`

**What it shows:** Raw metric queries (for debugging, not daily use)

**How to use:**
1. Type a metric name in the expression box: `allowed_requests_total`
2. Click Execute
3. Switch to Graph tab to see it over time

**Available metrics:**
| Metric | Meaning |
|--------|---------|
| `allowed_requests_total` | Total number of requests the firewall allowed |
| `blocked_requests_total` | Total number of requests the firewall blocked |
| `rate(allowed_requests_total[1m])` | Requests allowed per second (last 1 minute) |
| `rate(blocked_requests_total[1m])` | Requests blocked per second (last 1 minute) |

---

## CI/CD Pipeline Flow (Jenkins)

```
Developer pushes code to GitHub
         |
         v
Jenkins detects change (or manual Build Now)
         |
         v
+------------------+
| Stage: Checkout  |  Clone from https://github.com/dikshax86/NFV_SPE_MajorProject1.git
+--------+---------+
         |
         v
+------------------+
| Stage: Build     |  docker build -t dknights/firewall:v1 ./firewall-service
| Images           |  docker build -t dknights/switch:v1 ./switch-service
|                  |  docker build -t dknights/monitor:v1 ./monitor-service
+--------+---------+
         |
         v
+------------------+
| Stage: Login to  |  docker login -u dknights (using DockerHubCred)
| DockerHub        |
+--------+---------+
         |
         v
+------------------+
| Stage: Push      |  docker push dknights/firewall:v1
| Images           |  docker push dknights/switch:v1
|                  |  docker push dknights/monitor:v1
+--------+---------+
         |
         v
+------------------+
| Stage: Deploy to |  kubectl apply -f k8s/namespace.yaml
| Kubernetes       |  kubectl apply -f k8s/storage.yaml
|                  |  kubectl apply -f k8s/prometheus-config.yaml
|                  |  kubectl apply -f k8s/prometheus.yaml
|                  |  kubectl apply -f k8s/grafana.yaml
|                  |  kubectl apply -f k8s/elasticsearch.yaml
|                  |  kubectl apply -f k8s/kibana.yaml
|                  |  kubectl apply -f k8s/firewall-deployment.yaml
|                  |  kubectl apply -f k8s/monitor-deployment.yaml
|                  |  kubectl apply -f k8s/switch-deployment.yaml
|                  |  kubectl apply -f k8s/ingress.yaml
|                  |  kubectl rollout restart (all 3 services)
+------------------+
```

---

## Request Flow (End to End - Detailed)

```
1. User sends: POST http://nfv.local/route {"message": "hello"}
        |
        v
2. [NGINX Ingress Controller]
   - Receives the HTTP request
   - Matches host "nfv.local" and path "/"
   - Forwards to Switch service on port 5001
        |
        v
3. [Switch Service - port 5001]
   - Receives the request at /route
   - Extracts the X-Forwarded-For header (client IP)
   - Sends the request to Firewall at http://firewall:5000/check
   - Simultaneously sends to Monitor at http://monitor:5002/log
        |
        +-----> [Firewall Service - port 5000]
        |          - Receives the request
        |          - Checks if IP is in BLOCKED_IPS list
        |          - Checks if content contains BLOCKED_KEYWORDS
        |          - If blocked: increments blocked_requests_total metric, returns 403
        |          - If allowed: increments allowed_requests_total metric, returns 200
        |          - Exposes /metrics for Prometheus to scrape
        |
        +-----> [Monitor Service - port 5002]
        |          - Receives the request
        |          - Creates log entry: {ip, data, timestamp}
        |          - Stores in local memory (accessible via /logs)
        |          - Sends to Elasticsearch at http://elasticsearch:9200/logs/_doc
        |          - Retries up to 3 times if Elasticsearch is unavailable
        |
        v
4. [Switch returns Firewall's response to user]
   - {"status": "allowed"} with 200 OK
   - OR {"status": "blocked", "reason": "..."} with 403 Forbidden
```

---

## Monitoring Flow (Background - always running)

```
Every 5 seconds:
    Prometheus ----scrapes----> http://firewall:5000/metrics
                                     |
                                     v
                              allowed_requests_total = 12
                              blocked_requests_total = 5
                                     |
                                     v
    Prometheus stores this data point with timestamp
                                     |
                                     v
    Grafana queries Prometheus -----> Displays graphs/gauges on dashboard
```

---

## Logging Flow (on every request)

```
Every request:
    Monitor Service ----POST----> http://elasticsearch:9200/logs/_doc
                                         |
                                         v
                                  Stores document:
                                  {
                                    "ip": "192.168.49.1",
                                    "data": {"message": "hello"},
                                    "timestamp": "2026-05-15T15:39:51"
                                  }
                                         |
                                         v
    Kibana ----reads from----> Elasticsearch
                                         |
                                         v
                              User can search/filter logs in Kibana UI
```

---

## Kubernetes Concepts Used

| Concept | What it is | Where used |
|---------|-----------|------------|
| **Namespace** | Isolated environment for resources | `nfv-system` separates our project from others |
| **Deployment** | Manages pod replicas and updates | One per service (firewall, switch, monitor, etc.) |
| **Service (ClusterIP)** | Internal DNS name for pods | `firewall:5000`, `switch:5001`, `monitor:5002` |
| **Service (NodePort)** | Exposes a service on a fixed port on the node | Grafana (32210), Kibana (30602) |
| **Ingress** | Routes external HTTP traffic to services | Maps `nfv.local` to Switch service |
| **PersistentVolume** | Disk storage that survives pod restarts | Elasticsearch data at `/data/elasticsearch` |
| **PersistentVolumeClaim** | Request for storage by a pod | Elasticsearch requests 1Gi |
| **ConfigMap** | Stores configuration files | Prometheus scrape config (`prometheus.yml`) |

---

## Docker Images

| Image | Source | Description |
|-------|--------|-------------|
| `dknights/firewall:v1` | `firewall-service/Dockerfile` | Python Flask firewall app |
| `dknights/switch:v1` | `switch-service/Dockerfile` | Python Flask switch/router app |
| `dknights/monitor:v1` | `monitor-service/Dockerfile` | Python Flask logger app |
| `grafana/grafana` | Docker Hub (official) | Grafana visualization |
| `prom/prometheus` | Docker Hub (official) | Prometheus metrics collector |
| `docker.elastic.co/elasticsearch/elasticsearch:8.13.0` | Elastic (official) | Elasticsearch search engine |
| `docker.elastic.co/kibana/kibana:8.13.0` | Elastic (official) | Kibana log visualization |

---

## Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Application | Python, Flask | Microservices logic |
| Containerization | Docker | Package apps into containers |
| Orchestration | Kubernetes (Minikube) | Deploy, scale, manage containers |
| CI/CD | Jenkins (Pipeline) | Automate build, push, deploy |
| Image Registry | DockerHub (`dknights/`) | Store Docker images |
| Metrics Monitoring | Prometheus | Collect numerical metrics |
| Metrics Visualization | Grafana | Display metrics as dashboards |
| Log Storage | Elasticsearch | Store and search full logs |
| Log Visualization | Kibana | Browse and filter logs |
| Ingress | NGINX Ingress Controller | Route external traffic |
| Version Control | Git + GitHub | Source code management |

---

## Troubleshooting

### Pods stuck in ImagePullBackOff
The Docker images don't exist on DockerHub yet. Run the Jenkins pipeline to build and push them.

### Pods stuck in ContainerCreating
Minikube is pulling images from DockerHub. Wait 1-2 minutes.

### Pods in Terminating state
Normal. Happens after `kubectl rollout restart`. Old pods are shutting down while new ones start.

### Jenkins Deploy stage fails with "failed to download openapi"
Jenkins can't reach Minikube. Fix by copying fresh kubeconfig and certificates:
```bash
sudo cp ~/.kube/config /var/lib/jenkins/.kube/config
sudo cp ~/.minikube/ca.crt /var/lib/jenkins/.minikube/ca.crt
sudo cp ~/.minikube/profiles/minikube/client.crt /var/lib/jenkins/.minikube/profiles/minikube/client.crt
sudo cp ~/.minikube/profiles/minikube/client.key /var/lib/jenkins/.minikube/profiles/minikube/client.key
sudo chown -R jenkins:jenkins /var/lib/jenkins/.minikube /var/lib/jenkins/.kube
sudo sed -i "s|/home/$(whoami)/.minikube|/var/lib/jenkins/.minikube|g" /var/lib/jenkins/.kube/config
```

### Grafana shows "No data"
1. Check that Prometheus data source is configured: Connections -> Data sources -> Prometheus -> URL should be `http://prometheus:9090`
2. Send some test traffic first to generate metrics

### Elasticsearch logs are empty
1. Check Monitor pod logs: `kubectl logs deployment/monitor -n nfv-system`
2. Elasticsearch may still be starting up (takes ~30 seconds)
3. Send a test request to generate a log entry

---

## Useful Commands

```bash
# Check all resources
kubectl get all -n nfv-system

# Check pod logs
kubectl logs deployment/firewall -n nfv-system
kubectl logs deployment/switch -n nfv-system
kubectl logs deployment/monitor -n nfv-system

# Check pod status in detail
kubectl describe pod <pod-name> -n nfv-system

# Port-forward Prometheus (if needed)
kubectl port-forward svc/prometheus 9090:9090 -n nfv-system

# Restart a deployment (pulls latest image)
kubectl rollout restart deployment firewall -n nfv-system

# Delete everything and start fresh
kubectl delete namespace nfv-system

# Check minikube IP
minikube ip

# Check ingress
kubectl get ingress -n nfv-system
```
