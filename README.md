"# opentelemetry-metrics-collector-project" 
ML OpenTelemetry Sidecar Challenge
Candidate Instructions
Welcome! This is a hands-on coding challenge designed to evaluate your ability to work with OpenTelemetry in a real-world ML infrastructure scenario.

What You'll Do
Implement a metrics bridge sidecar that collects ML training metrics and exports them to an OpenTelemetry Collector using OTLP (OpenTelemetry Protocol).

Time Allocation
2-3 hours for a senior engineer familiar with OpenTelemetry concepts.

Choose Your Language
Implement the sidecar in either Python or Go (not both). Both languages have identical requirements - pick the one you're most comfortable with.

What We're Evaluating
Technical Skills: Correct implementation of OpenTelemetry instrumentation
Code Quality: Clean, maintainable, well-structured code
Kubernetes Knowledge: Proper sidecar pattern implementation in k8s/ml-training-job.yaml (REQUIRED)
Error Handling: Robust handling of edge cases and failures
Communication: Clear documentation of your design choices (REQUIRED - see submission.md)
Best Practices: Proper use of OpenTelemetry SDK and semantic conventions
Submission Requirements
Your PR must include:

Working code implementation (sidecar in Python or Go)
updated docker-compose.yaml with your sidecar added
Completed Kubernetes manifest k8s/ml-training-job.yaml with sidecar container (MANDATORY)
Completed submission.md explaining your design decisions (MANDATORY)
Important: Both the Kubernetes manifest completion (k8s/ml-training-job.yaml) and the submission.md documentation are not optional. We evaluate your ability to work with Kubernetes and communicate technical decisions as much as your code implementation.

A Note on Testing
We understand that this is a time-boxed challenge and we wish to be respectful of your time. At your level, we know you would not submit a pull request without comprehensive testing, but the time available for this task may make that impractical.

With that in mind, you can either:

Write some tests that demonstrate your testing strategy, then document the rest in your submission.md, OR
Simply document what you would have tested and how in your submission.md
Either approach is acceptable. Be prepared to discuss your testing strategy in detail during your follow-on interview.

Follow-On Interview
Be prepared to discuss your implementation in a technical interview where you will:

Walk through your code and explain your design choices
Answer questions about specific implementation details
Discuss trade-offs and alternative approaches you considered
Discuss your testing strategy (whether implemented or planned)
Debug or extend your solution in real-time
You must own and understand your code. Using AI or coding assistants is perfectly acceptable, but you are expected to understand what your code does and why you chose the patterns you implemented.

Getting Started
Read this README completely
Review the skeleton code in sidecar-python/ or sidecar-go/
Start the infrastructure with make dev-up
Implement the TODOs in your chosen language
Complete the Kubernetes manifest in k8s/ml-training-job.yaml by adding the sidecar container
Test with make verify
Document your choices in submission.md
Submit a PR
Task Description
The Challenge
You're working on an ML infrastructure platform that's integrating Prometheus and OpenTelemetry for observability. ML training jobs currently write metrics to a file in JSON format. Your task is to build a sidecar container that:

Reads ML training metrics from a shared volume (/shared/metrics/current.json)
Converts those metrics to OpenTelemetry format with appropriate instruments (Gauge, Counter, Histogram)
Exports them via OTLP to an OpenTelemetry Collector
Handles errors gracefully (file delays, parse errors, network issues)
Provides observability through proper logging and metric attributes
Why This Matters
This pattern is common in production ML platforms where:

Training jobs can't be modified to add direct instrumentation
Metrics need to be collected from heterogeneous sources
OpenTelemetry provides vendor-neutral observability
Sidecar pattern enables separation of concerns
The Sidecar Pattern
Your sidecar runs alongside the ML training job in the same Pod (Kubernetes) or network (Docker Compose), sharing a volume where metrics are written. This is a common pattern for adding observability without modifying application code.

Overview
This challenge simulates a real-world scenario of integrating Prometheus and OpenTelemetry in an ML infrastructure platform. You'll implement a sidecar container that:

Reads ML training metrics from a shared volume (written by the training job)
Converts those metrics to OpenTelemetry format
Exports them via OTLP to an OpenTelemetry Collector
Enables observation through Prometheus for verification
Architecture
┌─────────────────────────────────────────────────────────────┐
│  Pod / Docker Compose Network                               │
│                                                              │
│  ┌──────────────┐    ┌─────────────────┐                   │
│  │              │    │                 │                   │
│  │   ML Job     │───▶│  Shared Volume  │                   │
│  │  (Training)  │    │  /shared/metrics│                   │
│  │              │    │  current.json   │                   │
│  └──────────────┘    └────────┬────────┘                   │
│                               │                             │
│                               │ Read                        │
│                               ▼                             │
│                      ┌─────────────────┐                   │
│                      │   YOUR SIDECAR  │                   │
│                      │  (Python or Go) │                   │
│                      │                 │                   │
│                      │  - Read metrics │                   │
│                      │  - Convert      │                   │
│                      │  - Export OTLP  │                   │
│                      └────────┬────────┘                   │
│                               │                             │
└───────────────────────────────┼─────────────────────────────┘
                                │ OTLP/gRPC
                                │ (port 4317)
                                ▼
                    ┌────────────────────────┐
                    │  OpenTelemetry         │
                    │  Collector             │
                    │  - Receive OTLP        │
                    │  - Export Prometheus   │
                    └───────────┬────────────┘
                                │
                                │ Scrape (port 8889)
                                ▼
                        ┌───────────────┐
                        │  Prometheus   │
                        │  (Verification)│
                        └───────────────┘
Language Choice
You can implement the sidecar in Python OR Go. Both have identical functional requirements:

Python
SDK: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp
Directory: sidecar-python/
Go
SDK: go.opentelemetry.io/otel/*
Directory: sidecar-go/
Quick Start
Prerequisites
Docker and Docker Compose
Make (optional, but recommended)
For Go: Go 1.24+ (for local development)
For Python: Python 3.12+ (for local development)
1. Start the Infrastructure
# Start OpenTelemetry Collector, Prometheus, and Mock ML Job
make dev-up

# Or without Make:
docker-compose up -d
This starts:

OpenTelemetry Collector on ports 4317 (OTLP gRPC), 8889 (Prometheus metrics)
Prometheus on port 9090
Mock ML Training Job writing metrics every 10 seconds
2. Choose Your Language and Implement
Choose either Python or Go and implement the sidecar look at the README in the respective directory for more details.

3. Add Your Sidecar to Docker Compose
Edit docker-compose.yml and add the sidecar for your chosen language:

example:

sidecar-python:
  build: ...
4. Build and Run
# Build your sidecar
make build-python  # or make build-go

# Restart the environment
make dev-down
make dev-up
5. Verify Metrics Flow
# Check that metrics are flowing
make verify

# View your sidecar logs
make logs-sidecar-python  # or make logs-sidecar-go

# View collector logs
make logs-collector

# Open Prometheus UI
open http://localhost:9090
Manual Verification with Prometheus Queries
You can manually verify metrics are flowing by querying Prometheus at http://localhost:9090. Here are some sample queries:

Basic Metric Queries
# Check training loss over time
ml_metrics_ml_training_loss

# Check validation loss
ml_metrics_ml_training_validation_loss

# Check accuracy
ml_metrics_ml_training_accuracy

# Check GPU utilization
ml_metrics_ml_training_gpu_utilization

# Check learning rate
ml_metrics_ml_training_learning_rate
Filtered by Attributes
# Metrics for a specific model
ml_metrics_ml_training_loss{model_name="resnet-50"}

# Metrics for a specific job
ml_metrics_ml_training_accuracy{job_id="training-job-123"}

# Metrics for a specific dataset
ml_metrics_ml_training_accuracy{dataset="imagenet"}
Counter Metrics
# Total number of batches processed
ml_metrics_ml_training_batch_number

# Current epoch
ml_metrics_ml_training_epoch
Histogram Metrics
# Processing time distribution
ml_metrics_ml_training_processing_time_ms

# Samples per second histogram
ml_metrics_ml_training_samples_per_second

# Get average processing time (if histogram)
rate(ml_metrics_ml_training_processing_time_ms_sum[5m]) / rate(ml_metrics_ml_training_processing_time_ms_count[5m])
Aggregated Queries
# Average training loss across all models
avg(ml_metrics_ml_training_loss)

# Max GPU utilization
max(ml_metrics_ml_training_gpu_utilization)

# Training loss rate of change
rate(ml_metrics_ml_training_loss[1m])
Command Line Verification
# Query Prometheus metrics endpoint directly
curl -s http://localhost:8889/metrics | grep ml_metrics

# Check for specific metric
curl -s http://localhost:8889/metrics | grep ml_training_loss

# Count how many ML metrics are exported
curl -s http://localhost:8889/metrics | grep "^ml_metrics" | wc -l

# View metrics with their labels
curl -s http://localhost:8889/metrics | grep ml_metrics | grep -v "^#"
What You Need to Implement
Core Requirements
OpenTelemetry SDK Initialization

Set up OTLP exporter with collector endpoint from env var
Configure MeterProvider with service resource
Create meter for the service
Metric Instruments

Create appropriate instruments for ML metrics:
Gauges: training_loss, validation_loss, accuracy, learning_rate, gpu_utilization
Counters: batch_number, epoch
Histograms: processing_time_ms, samples_per_second
Metrics Collection Loop

Read /shared/metrics/current.json at regular intervals
Parse JSON safely with error handling
Handle file not existing initially (ML job startup delay)
Metrics Conversion

Extract job metadata (job_id, model_name, dataset)
Map each metric to appropriate OTel instrument
Add attributes: job.id, model.name, dataset, epoch, batch
Error Handling

Graceful handling of missing/malformed files
Continue running despite errors (don't crash)
Proper logging at appropriate levels
Graceful shutdown on SIGTERM/SIGINT
Metrics JSON Format
The ML job writes this format to /shared/metrics/current.json:

{
  "timestamp": "2024-10-22T10:30:00Z",
  "job_metadata": {
    "job_id": "training-job-123",
    "model_name": "resnet-50",
    "dataset": "imagenet",
    "start_time": "2024-10-22T10:00:00Z"
  },
  "training_metrics": {
    "epoch": 5,
    "batch_number": 150,
    "training_loss": 0.342,
    "validation_loss": 0.389,
    "accuracy": 0.876,
    "learning_rate": 0.001,
    "gpu_utilization": 0.94,
    "processing_time_ms": 245,
    "samples_per_second": 156.2
  }
}
Environment Variables
Your sidecar should support these environment variables:

OTEL_EXPORTER_OTLP_ENDPOINT: Collector endpoint (e.g., otel-collector:4317)
OTEL_SERVICE_NAME: Service name (e.g., ml-metrics-bridge)
METRICS_FILE_PATH: Path to metrics file (default: /shared/metrics/current.json)
COLLECTION_INTERVAL: Polling interval in seconds (default: 10)
LOG_LEVEL: Logging verbosity (default: INFO or info)
Helpful Commands
# Development
make dev-up              # Start all services
make dev-down            # Stop all services
make verify              # Check metrics are flowing

# Building
make build-python        # Build Python sidecar
make build-go            # Build Go sidecar

# Logs
make logs-sidecar-python # Python sidecar logs
make logs-sidecar-go     # Go sidecar logs
make logs-ml             # ML training job logs
make logs-collector      # OTel collector logs
make logs-all            # All logs

# Cleanup
make clean               # Remove containers and volumes

# Kubernetes (optional)
make k8s-deploy          # Deploy to Kubernetes
make k8s-delete          # Delete from Kubernetes
make k8s-logs-sidecar    # View sidecar logs in K8s
Submission
Create a Pull Request with your implementation that includes:

Code Implementation (Required)

Implemented sidecar files (main.py/main.go and config.py/config.go)
Updated docker-compose.yml with your sidecar
Any additional dependencies added to requirements.txt or go.mod
Kubernetes Manifest (Required - NOT OPTIONAL)

Completed k8s/ml-training-job.yaml with sidecar container configuration
This demonstrates your understanding of the sidecar pattern in Kubernetes
Must include: sidecar container definition, environment variables, volume mounts, resource limits
The sidecar should be configured to work with the existing otel-collector service
Documentation (Required - NOT OPTIONAL)

Completed submission.md file explaining your design choices
This is mandatory - we evaluate communication and decision-making as much as code quality
Use the provided template as your starting point
Include: design choices, architecture decisions, trade-offs, error handling strategy
Evaluation Criteria
Your implementation will be evaluated on:

Correctness (25%): Does the sidecar correctly read, convert, and export metrics?
Code Quality (20%): Clean, readable, well-structured code with proper organization
Kubernetes Manifest (15%): Correctly configured sidecar in k8s/ml-training-job.yaml (mandatory)
Proper sidecar container configuration
Correct environment variables and volume mounts
Appropriate resource limits
Integration with otel-collector service
Error Handling (15%): Graceful handling of edge cases and errors
Documentation (15%): Clear explanation of design choices in submission.md (mandatory)
OpenTelemetry Best Practices (10%): Proper use of OTel SDK, semantic conventions, instrument types
Note: Missing or incomplete submission.md documentation OR incomplete Kubernetes manifest (k8s/ml-training-job.yaml) will result in an automatic rejection, regardless of code quality. We need to see both your implementation skills and your understanding of Kubernetes deployment patterns.

Resources
Python OpenTelemetry
OpenTelemetry Python Docs
Python SDK Reference
OTLP Exporter
Go OpenTelemetry
OpenTelemetry Go Docs
Go SDK Reference
OTLP Exporter
General
OpenTelemetry Semantic Conventions
OTLP Specification
Time Expectation
This challenge is designed to take 2-3 hours for a senior engineer familiar with OpenTelemetry concepts:

1.5-2 hours: Implementation and testing
30-45 minutes: Documentation (submission.md)
15 minutes: Verification and final review
Budget your time accordingly - don't spend 3 hours on code and rush the documentation!

Before You Submit
 Code implements all core requirements
 make verify shows metrics flowing to Prometheus
 All error cases are handled gracefully
 docker-compose.yml has your sidecar
 k8s/ml-training-job.yaml is complete with sidecar container configuration ← Don't forget!
 submission.md is complete with thoughtful explanations ← Don't forget!
 You've tested the full end-to-end flow
 Dependencies are properly listed
Questions?
If you have questions about the challenge requirements, please reach out. We're happy to clarify!