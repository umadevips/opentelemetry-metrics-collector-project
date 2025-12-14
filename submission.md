Submission: OpenTelemetry Metrics Bridge Implementation
Document your implementation: design choices, architectural decisions, trade-offs, error handling strategy, Kubernetes manifest configuration, and testing approach.

Your documentation here

# Submission
# Metrics Bridge Sidecar Implementation using Python

## Overview
This implementation provides a production ready sidecar container which collects the ML training metrics from a shared json file, converts the metrics to telemtry supported instruments and sends to the otel collector using otlp and further sends these metrics to the backend of our choice which is prometheus in this use case.

## Key decisions:

- **Architecture:** Sidecar pattern chosen over alternatives (node agent, push model) for isolation and flexibility
- **Metric Instruments:** Observable pattern for consistency, appropriate type selection (Gauge/Counter/Histogram)
- **Error Resilience:** Graceful degradation on file/network errors, no crashes, auto-recovery
- **Security:** Non-root execution, least privilege, cluster-internal communication
- **Performance:** <5% CPU, <100MB RAM, 0-30s end-to-end latency
- **Operations:** Comprehensive logging, self-monitoring metrics, graceful shutdown

**Production Ready:** Deployed and tested in Docker Compose and Kubernetes environments.

### Architecture
```

┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Pod / Docker Network      │
│                                                         │
│  ┌─────────────────┐         ┌──────────────────────┐   │
│  │  ML Training    │         │  OTel Metrics Bridge │   │
│  │  Container      │         │  Sidecar             │   │
│  │                 │ pull-based                     │   │
│  │  Writes JSON ──────────>  │  Reads JSON          │   │
│  │  to /shared     │         │  Converts to OTel    │   │
│  └─────────────────┘         │  Exports via OTLP    │   │
│         │                    └──────────────────────┘   │
│         │                        │                      │
│         └───Shared Volume ───────┘                      │
│       (shared/metrics/current.json)                     │
└─────────────────────────────────────────────────────────┘
                                         │
                                         │ OTLP
                                         ▼
                    ┌────────────────────────┐
                    │  OpenTelemetry         │
                    │  Collector             │
                    │  ┌──────────────────┐  │(push based)
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
                    │  (Verification)        │
                    └────────────────────────┘
```

### Alternative architectures considered
### Push vs Pull model
**Rejected: having ML job push directly to Otel**
- **Why rejected:**
    - it requires modifying ML training code
    - created coupling bewteen training logic and observability
    - harder to update observability without retraining
- **Trade off:** Sidecar adds slight complexitybut maintains separation.

### Agent vs SIdecar pattern
**Rejected: Node level deamonset agent**
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
- **trafe off:** 10s latency is ok for traning metrics

### Direct Prometheus exposition vs Otlp
**Rejected: Sidecar with metrics endpoint**
- **WHy rejected:**
    - it requires prometheus to scrape every pod
    - it is harder to add tracing or logs later
    - pull model doesnt fit ephemeral jobs well
- **Trade off:** otlp is push based and fits job pattern better

## Sidecar pattern benefits
1. No modification to ML code is required
2. Training logic separates from observability
3. Same sidecar works with any json wirting job
4. Training continues even if metrics export fails

# Design decisions
## Metrics instrument selection
### Gauges (Instantaneous values that goes up/down)
- **ml.training.loss**: training loss fluctuates based on current batch
- **ml.validation.loss**: validation loss represents current model performance
- **ml.training.accuracy**: accuracy metric
- **ml.training.learning_rate**: it changes during training
- **ml.training.gpu_utilization**: real time gpu usagepercentage

### Counters (monotonically increasing values)
- **ml.training.batch_number**: cumulative batch count
- **ml.training.epoch**: cumulative epoch count

### Histograms (distribution of values over time)
- **ml.training.processing_time**: batch processing time distribution
- **ml.training.samples_per_second**: throughput ditribution

**Note**: This mapping follows otel semantic convention.

### Configuration management
Environment based configuration with validation  
    - *OTEL_EXPORTER_OTLP_ENDPOINT*  
    - *OTEL_SERVICE_NAME*  
    - *METRICS_FILE_PATH*  
    - *COLLECTION_INTERVAL*  
    - *LOG_LEVEL*  


### Error handling strategy
**1.File not found**
if not metrics_path.exists():
    self.logger.debug("Metrics file does not exist yet")
    return None
**Scenario**: Sidecar starts before ML job writes first metrics
**Handling**: Log at DEBUG level, continue polling. This is expected behaviour.

**2. Malformed Json**
except json.JSONDecodeError as e:
    self.logger.error(f"Failed to parse metrics JSON: {e}")
    return None
**Scenario**: Partial write, corrupted file, invalid format
**Handling**: Log error, skip this iteration, continue polling

**3. Network failure (OTLP export)**
Opentelemetry SDK handles exportretries automatically
    - Queuing of metrics during outages
    - Automatic reconnection
**Handling**: rely on SDK and log only critical features

**4. Resourc exhaustion**
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
**Protection**:
    - Memory limits prevent OOM
    - CPU limits prevent starving main container
    
**5. Graceful shutdown**
signal.signal(signal.SIGTERM, self._signal_handler)
signal.signal(signal.SIGINT, self._signal_handler)

**On SIGTERM/SIGINIT:**
    1. Stop collection loop
    2. Flush remaining metrics via provider.shutdown()
    3. Complete pending exports
    4. Exit cleanly

### Kubernetes integration:
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]
15 second grace period ensure final metrics export before pod termination.

### Trade offs
## 1. Polling vs. Watching
**Choice:** Polling (Sleep interval)
**Alternatives considered:**























# Security Considerations:
**Assets to protect:**
- ML training metrics
- Otel collector end points
- Pod resou\rces

Currently no TLS for otlp is present. In production env, enable tls for otlp with cert manager is recommended.

# Scaling


