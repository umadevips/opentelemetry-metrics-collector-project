Submission: OpenTelemetry Metrics Bridge Implementation
Document your implementation: design choices, architectural decisions, trade-offs, error handling strategy, Kubernetes manifest configuration, and testing approach.

Your documentation here

# Submission
# Metrics Bridge Sidecar Implementation using Python

## Overview
This implementation provides a production ready sidecar container which collects the ML training metrics from a shared json file, converts the metrics to telemetry supported instruments and sends to the otel collector using otlp and further sends these metrics to the backend of our choice which is prometheus in this use case.

### Key decisions:

- **Architecture:** Sidecar pattern chosen over alternatives (node agent, push model) for isolation and flexibility
- **Metric Instruments:** Observable pattern for consistency, appropriate type selection (Gauge/Counter/Histogram)
- **Error Resilience:** Graceful degradation on file/network errors, no crashes, auto-recovery
- **Security:** Non-root execution, least privilege, cluster-internal communication
- **Performance:** <5% CPU, <100MB RAM, 0-30s end-to-end latency
- **Operations:** Comprehensive logging, self-monitoring metrics, graceful shutdown

### Architecture
```

┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Pod                       │
│                                                         │
│  ┌─────────────────┐         ┌──────────────────────┐   │
│  │  ML Training    │         │  OTel Metrics Bridge │   │
│  │  Container      │         │  Sidecar             │   │
│  │                 │                                │   │
│  │  Writes JSON ──────────>  │  Reads JSON          │   │
│  │  to /shared     │         │  Converts to OTel    │   │
│  └─────────────────┘         │  Exports via OTLP    │   │
│         │                    └──────────────────────┘   │
│         │                        │                      │
│         └───Shared Volume ───────┘                      │
│       (shared/metrics/current.json)                     │
└─────────────────────────────────────────────────────────┘
                                         │
                                         │ OTLP/gRPC
                                         ▼
                    ┌────────────────────────┐
                    │  OpenTelemetry         │
                    │  Collector             │
                    │  ┌──────────────────┐  │
                    │  │ Receives OTLP    │  │
                    │  │                  │  │
                    │  │ Export Prometheus|  │
                    │  └──────────────────┘  │
                    └────────────────────────┘
                                 │
                                 │ HTTP Scrape
                                 ▼
                    ┌────────────────────────┐
                    │  Prometheus            │
                    │                        │
                    └────────────────────────┘
```
## Sidecar pattern benefits
1. No modification to ML code is required
2. Training logic separates from observability
3. Same sidecar works with any json writing job
4. Training continues even if metrics export fails

### Alternative architectures considered
### Push vs Pull model
**Rejected: having ML job push directly to Otel**
- **Why rejected:**
    - it requires modifying ML training code
    - created coupling between training logic and observability
    - harder to update observability without retraining
- **Trade off:** Sidecar adds slight complexity but maintains separation.

### Agent vs SIdecar pattern
**Rejected: Node level daemonset agent**
- **Why rejected:**
    - shared agent created blast radius which affects all pods on node
    - harder to version per job
    - volume sharing across pods is complex
- **Trade off:** Per pod sidecar uses more resources but better isolation

### Event-driven vs Polling
**Rejected: File system watching (inotify)**
- **WHy rejected:**
    - platform specific to linux only
    - more complex error handling
    - all container runtimes do not support inotify
- **trade off:** 10s latency is ok for training metrics

### Direct Prometheus exposition vs Otlp
**Rejected: Sidecar with metrics endpoint**
- **Why rejected:**
    - it requires prometheus to scrape every pod
    - it is harder to add tracing or logs later
    - pull model doesnt fit ephemeral jobs well
- **Trade off:** otlp is push based and fits job pattern better

### Json file format  
  Continue using json format,  
    - it is easy for debugging and human readable  
    - it is widely supported as any language can write  
    - it doesnt break existing ml jobs

## Security Considerations:
**Assets to protect:**
- ML training metrics
- Otel collector end points
- Pod resou\rces    
**Insecure grpc connection:**  
```python
exporter = OTLPMetricExporter(
    endpoint=self.config.otel_endpoint,
    insecure=True)
``` 
**Note:** insecure=true for internal cluster communication  
Currently no TLS for otlp is present. In production env, enabling tls for otlp with cert manager is recommended.

# Design decisions
## Metrics instrument selection
### Gauges (Instantaneous values that goes up/down)
- **ml.training.loss**: training loss fluctuates based on current batch
- **ml.validation.loss**: validation loss represents current model performance
- **ml.training.accuracy**: accuracy metric
- **ml.training.learning_rate**: it changes during training
- **ml.training.gpu_utilization**: real time gpu usage percentage

### Counters (monotonically increasing values)
- **ml.training.batch_number**: cumulative batch count
- **ml.training.epoch**: cumulative epoch count

### Histograms (distribution of values over time)
- **ml.training.processing_time**: batch processing time distribution
- **ml.training.samples_per_second**: throughput distribution

**Note**: This mapping follows otel semantic convention.

## Configuration management
Environment based configuration with validation:  
- `OTEL_EXPORTER_OTLP_ENDPOINT` - OpenTelemetry Collector endpoint
- `OTEL_SERVICE_NAME` - Service identifier
- `METRICS_FILE_PATH` - Path to metrics JSON file
- `COLLECTION_INTERVAL` - Polling frequency in seconds
- `LOG_LEVEL` - Logging verbosity

## Error handling strategy
**1. File not found** (cold start scenario) 
```python
if not metrics_path.exists():  
    self.logger.debug("Metrics file does not exist yet")  
    return None  
```
**Scenario:** Sidecar starts before ML job writes first metrics  
**Handling:** Log at DEBUG level, continue polling. This is expected behaviour.

**2. Malformed Json**  
```python
except json.JSONDecodeError as e:  
    self.logger.error(f"Failed to parse metrics JSON: {e}")  
    return None  
```
**Scenario:** Partial write, corrupted file, invalid format  
**Handling:** Log error, skip this iteration, continue polling

**3. Network failure (OTLP export)**  
Opentelemetry SDK provides automatic retry logic:  
- Queuing of metrics during outages  
- Automatic reconnection  
**Handling:** rely on SDK and log only critical features

**4. Resource exhaustion**  
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m" 
``` 
**Protection Mechanisms**:  
    - Memory limits prevent OOM by killing other containers 
    - CPU limits prevent starving main ml container
    
**5. Graceful shutdown**  
```python
    signal.signal(signal.SIGTERM, self._signal_handler)  
    signal.signal(signal.SIGINT, self._signal_handler) 
 ``` 
    **Shutdown sequence (on SIGTERM/SIGINT):**  
    1. Stop collection loop  
    2. Flush remaining metrics via provider.shutdown()  
    3. Complete pending exports  
    4. Exit cleanly

### Kubernetes integration:  
```yaml
lifecycle:  
  preStop:  
    exec:  
      command: ["/bin/sh", "-c", "sleep 15"]  
```
15 second grace period ensure final metrics export before pod termination.

# Scaling  
**Horizontal scaling:**  
- each pod has its own sidecar  
- no shared state between sidecars  
 
**Bottlenecks:**  
- otel collector becomes bottleneck at ~1000 sidecars  
- mitigation: multiple collector replicas with load balancing

# Kubernetes manifest configuration
## Sidecar container specification  
```python
    - name: otel-metrics-bridge  
      image: ml-metrics-bridge:latest  
      imagePullPolicy: IfNotPresent  
```

### Key configurations:
1. **REsource limits:** conservative allocation  

- Requests: 128Mi RAM, 100m CPU  
- Limits: 256Mi RAM, 200m CPU  
- Reason: metrics collection is lightweight  

2. **Environment variables:** explicit configuration  
- name: OTEL_EXPORTER_OTLP_ENDPOINT  
  value: "otel-collector:4317"  
- using k8s DNS for service discovery  
- no hardcoded IPs  

3. **Volume Mount:** Read only access  
volumeMounts:  
    - name: metrics-volume  
      mountPath: /shared/metrics  
      readOnly: true  
    - principle of least privilege  
    - prevents accidental file modification  

4. **Lifecycle hooks:** Graceful termination  
```python
lifecycle:  
    preStop:
       exec:
         command: ["/bin/sh", "-c", "sleep 15"]  
```  
- allows final metric export  
- coordinates with k8s termination grace period  

## Volume configuration
```yml
    volumes:
  - name: metrics-volume
    emptyDir: {}  
```  
- automatic cleanup on pod deletion    
- fast and no external dependencies

# Testing approach
### 1. Local development testing
**Terminal 1: Start infrastructure**  
```bash
    docker-compose up otel-collector prometheus mock-ml-job
```

**Terminal 2: Build and run sidecar**  

```bash
cd sidecar-python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
export METRICS_FILE_PATH=/tmp/metrics/current.json
python main.py  
```  

**Validation**  
    1. check sidecar logs for successful initialization  
    2. verify otlp connection to collector  
    3. monitor metric exports every 10s  

### 2. Docker compose testing  
Build and start all services
```bash
docker-compose up --build
```  

Verify services running
```bash
docker-compose ps
```  
Check sidecar logs
```bash
docker-compose logs -f sidecar-python
```  
Verify metrics in Prometheus
open http://localhost:9090
Query: ml_training_loss  

### 3.Kubernetes testing  
Check pod status
```bash
kubectl get pods -n ml-otel-demo -w
```
**View sidecar logs**  
```bash
kubectl logs -n ml-otel-demo ml-training-<pod-id> -c otel-metrics-bridge -f
```  
**Deploy ML training job with sidecar**  
```bash
kubectl apply -f k8s/ml-training-job.yaml  
```

### 4. Error condition testing  
**Testcase 1: Missing metrics file**  
- Start sidecar without ML job
```bash
    docker-compose up sidecar-python 
``` 
**Expected:** DEBUG logs "Metrics file does not exist yet"  
Sidecar should continue running, polling

**Testcase 2: Malformed Json** 
- Write invalid JSON  
```bash
    echo "invalid json" > /path/to/metrics/current.json  
```
**Expected:**  ERROR log with JSON parse error  
Sidecar continues, next poll succeeds when file corrected  
 
**Testcase 3: Collector unavailable**  
- Stop collector
```bash
    docker-compose stop otel-collector 
``` 
**Expected:** OpenTelemetry SDK retries with backoff  
Metrics queued in memory  
Resume exporting when collector restarts

**Testcase 4: Resource limits**
- Set very low memory limit in K8s manifest
    limits:
     memory: "64Mi"  
- Monitor pod
```bash
    kubectl top pods -n ml-otel-demo  
```
**Expected:** Potential OOMKill if limit too low  
    Adjust limits based on actual usage patterns   

### Performance testing
- Increase metric write frequency  
```bash
    export WRITE_INTERVAL=1
    export COLLECTION_INTERVAL=1
```
- Monitor resource usage  
```bash
    docker stats sidecar-python
```
**Expected metrics:**
    - CPU: < 5% steady state
    - Memory: < 50Mi steady state
    - Network: < 1Mbps  






























