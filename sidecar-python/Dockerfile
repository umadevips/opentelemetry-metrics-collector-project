FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 sidecar

# Set working directory
WORKDIR /app

# Copy requirements and install dependenciess
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .

 # ENV METRICS_FILE_PATH=/shared/current.json
 # ENV COLLECTION_INTERVAL=10
 # ENV OTEL_EXPORTER_OTLP_ENDPOINT=otel-collector:4317
 # ENV OTEL_SERVICE_NAME=ml-metrics-bridge
 # ENV LOG_LEVEL=INFO
 # ENV SIDE_CAR_PROM_PORT=8000 '''

# Switch to non-root user
USER sidecar

# Run the sidecar
CMD ["python", "-u", "main.py"]