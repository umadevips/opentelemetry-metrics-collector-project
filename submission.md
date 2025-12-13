Submission: OpenTelemetry Metrics Bridge Implementation
Document your implementation: design choices, architectural decisions, trade-offs, error handling strategy, Kubernetes manifest configuration, and testing approach.

Your documentation here

# Submission: Metrics Bridge Sidecar Implementation using Python

## Overview
    This implementation provides a production ready sidecar container which collects the ML training metrics from a shared json file, converts the metrics to telemtry supported instruments and sends to the otel collector using otlp and further sends these metrics to the backend of our choice which is prometheus in this use case.

### Architecture

    ┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Pod / Docker Network          │
│                                                             │
│  ┌─────────────────┐         ┌──────────────────────┐       │
│  │  ML Training    │         │  OTel Metrics Bridge │       │
│  │  Container      │         │  Sidecar             │       │
│  │                 │         │                      │       │
│  │  Writes JSON ──────────>  │  Reads JSON          │       │
│  │  to /shared     │         │  Converts to OTel    │       │
│  └─────────────────┘         │  Exports via OTLP    │       │
│         │                    └──────────────────────┘       │
│         │                              │                    │
│         └──────── Shared Volume ───────┘                    │
│                   (shared/metrics/current.json)             │
└─────────────────────────────────────────────────────────┘
                                 │
                                 │ OTLP
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
                    │  (Verification)        │
                    └────────────────────────┘


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

## Counters (monotonically increasing values)
- **ml.training.batch_number**: cumulative batch count
- **ml.training.epoch**: cumulative epoch count

## Histograms (distribution of values over time)
- **ml.training.processing_time**: batch processing time distribution
- **ml.training.samples_per_second**: throughput ditribution

**Note**: This mapping follows otel semantic convention.



