Python Sidecar Implementation
Setup
Create a virtual environment and install dependencies:

cd sidecar-python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
Local Development
# Run locally (requires environment variables)
export OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317
export METRICS_FILE_PATH=/path/to/metrics/current.json
python main.py
Docker Build
# From repository root
make build-python

# Or directly with docker-compose
docker-compose build sidecar-python
Implementation Notes
Review the TODOs in:

main.py - Core sidecar logic (MetricsBridge class)
config.py - Configuration management
Key areas to implement:

OpenTelemetry SDK initialization
Metric instrument creation (Gauges, Counters, Histograms)
File reading and JSON parsing
Metrics conversion with attributes
Collection loop with error handling
Signal handling for graceful shutdown