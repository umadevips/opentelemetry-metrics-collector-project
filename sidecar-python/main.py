#!/usr/bin/env python3
"""
OpenTelemetry Metrics Bridge Sidecar

This sidecar collects ML training metrics from a shared volume
and exports them via OpenTelemetry Protocol (OTLP).
"""
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

from config import Config


class MetricsBridge:
    """Bridge between file-based metrics and OpenTelemetry."""
    
    def __init__(self, config: Config):
        """Initialize the metrics bridge."""
        self.config = config
        self.running = True
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenTelemetry
        self._init_otel()
        
        # Create metric instruments
        self._create_instruments()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _init_otel(self):
        """Initialize OpenTelemetry SDK with OTLP exporter."""
        self.logger.info(f"Initializing OpenTelemetry with endpoint: {self.config.otel_endpoint}")
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": self.config.service_name,
            "service.version": "1.0.0",
        })
        
        # Create OTLP exporter
        exporter = OTLPMetricExporter(
            endpoint=self.config.otel_endpoint,
            insecure=True  # Using insecure for internal cluster communication
        )
        
        # Create metric reader with periodic export
        reader = PeriodicExportingMetricReader(
            exporter=exporter,
            export_interval_millis=5000  # Export every 5 seconds
        )
        
        # Create and set meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[reader]
        )
        metrics.set_meter_provider(provider)
        
        # Get meter for creating instruments
        self.meter = metrics.get_meter(
            name=self.config.service_name,
            version="1.0.0"
        )
        
        self.logger.info("OpenTelemetry initialized successfully")
    
    def _create_instruments(self):
        """Create metric instruments for ML training metrics."""
        self.logger.info("Creating metric instruments")
        
        # Gauges for instantaneous values
        self.training_loss = self.meter.create_observable_gauge(
            name="ml.training.loss",
            description="Training loss value",
            callbacks=[self._get_training_loss]
        )
        
        self.validation_loss = self.meter.create_observable_gauge(
            name="ml.validation.loss",
            description="Validation loss value",
            callbacks=[self._get_validation_loss]
        )
        
        self.accuracy = self.meter.create_observable_gauge(
            name="ml.training.accuracy",
            description="Model accuracy",
            callbacks=[self._get_accuracy]
        )
        
        self.learning_rate = self.meter.create_observable_gauge(
            name="ml.training.learning_rate",
            description="Current learning rate",
            callbacks=[self._get_learning_rate]
        )
        
        self.gpu_utilization = self.meter.create_observable_gauge(
            name="ml.training.gpu_utilization",
            description="GPU utilization percentage",
            callbacks=[self._get_gpu_utilization]
        )
        
        # Counters for cumulative values
        self.batch_counter = self.meter.create_observable_counter(
            name="ml.training.batch_number",
            description="Current batch number",
            callbacks=[self._get_batch_number]
        )
        
        self.epoch_counter = self.meter.create_observable_counter(
            name="ml.training.epoch",
            description="Current epoch number",
            callbacks=[self._get_epoch]
        )
        
        # Histograms for distributions
        self.processing_time = self.meter.create_histogram(
            name="ml.training.processing_time",
            description="Processing time in milliseconds",
            unit="ms"
        )
        
        self.samples_per_second = self.meter.create_histogram(
            name="ml.training.samples_per_second",
            description="Training samples processed per second",
            unit="samples/s"
        )
        
        # Store current metrics for observable callbacks
        self.current_metrics: Optional[Dict[str, Any]] = None
        
        self.logger.info("Metric instruments created successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.running = False
    
    def _read_metrics_file(self) -> Optional[Dict[str, Any]]:
        """Read and parse metrics from JSON file."""
        metrics_path = Path(self.config.metrics_file_path)
        
        try:
            if not metrics_path.exists():
                self.logger.debug(f"Metrics file does not exist yet: {metrics_path}")
                return None
            
            with open(metrics_path, 'r') as f:
                data = json.load(f)
            
            # Validate structure
            if 'job_metadata' not in data or 'training_metrics' not in data:
                self.logger.warning("Invalid metrics file structure")
                return None
            
            return data
        
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse metrics JSON: {e}")
            return None
        
        except IOError as e:
            self.logger.error(f"Failed to read metrics file: {e}")
            return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error reading metrics: {e}")
            return None
    
    def _get_attributes(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract attributes from metrics data."""
        metadata = metrics_data.get('job_metadata', {})
        training = metrics_data.get('training_metrics', {})
        
        return {
            'job.id': metadata.get('job_id', 'unknown'),
            'model.name': metadata.get('model_name', 'unknown'),
            'dataset': metadata.get('dataset', 'unknown'),
            'epoch': training.get('epoch', 0),
            'batch': training.get('batch_number', 0),
        }
    
    # Observable callbacks for gauges and counters
    def _get_training_loss(self, options):
        """Callback for training loss gauge."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            loss = training.get('training_loss')
            if loss is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(loss, attrs)
    
    def _get_validation_loss(self, options):
        """Callback for validation loss gauge."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            loss = training.get('validation_loss')
            if loss is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(loss, attrs)
    
    def _get_accuracy(self, options):
        """Callback for accuracy gauge."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            acc = training.get('accuracy')
            if acc is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(acc, attrs)
    
    def _get_learning_rate(self, options):
        """Callback for learning rate gauge."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            lr = training.get('learning_rate')
            if lr is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(lr, attrs)
    
    def _get_gpu_utilization(self, options):
        """Callback for GPU utilization gauge."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            gpu = training.get('gpu_utilization')
            if gpu is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(gpu, attrs)
    
    def _get_batch_number(self, options):
        """Callback for batch counter."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            batch = training.get('batch_number')
            if batch is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(batch, attrs)
    
    def _get_epoch(self, options):
        """Callback for epoch counter."""
        if self.current_metrics:
            training = self.current_metrics.get('training_metrics', {})
            epoch = training.get('epoch')
            if epoch is not None:
                attrs = self._get_attributes(self.current_metrics)
                yield metrics.Observation(epoch, attrs)
    
    def _process_metrics(self, metrics_data: Dict[str, Any]):
        """Process metrics and record histogram values."""
        training = metrics_data.get('training_metrics', {})
        attrs = self._get_attributes(metrics_data)
        
        # Record histogram values (these use direct recording, not callbacks)
        processing_time = training.get('processing_time_ms')
        if processing_time is not None:
            self.processing_time.record(processing_time, attrs)
        
        samples_per_sec = training.get('samples_per_second')
        if samples_per_sec is not None:
            self.samples_per_second.record(samples_per_sec, attrs)
    
    def run(self):
        """Main collection loop."""
        self.logger.info(f"Starting metrics collection loop (interval: {self.config.collection_interval}s)")
        self.logger.info(f"Monitoring file: {self.config.metrics_file_path}")
        
        while self.running:
            try:
                # Read metrics from file
                metrics_data = self._read_metrics_file()
                
                if metrics_data:
                    # Store current metrics for observable callbacks
                    self.current_metrics = metrics_data
                    
                    # Process histogram metrics
                    self._process_metrics(metrics_data)
                    
                    self.logger.debug(f"Processed metrics: epoch={metrics_data.get('training_metrics', {}).get('epoch')}, "
                                     f"batch={metrics_data.get('training_metrics', {}).get('batch_number')}")
                else:
                    self.logger.debug("No valid metrics data available")
                
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}", exc_info=True)
            
            # Sleep for collection interval
            time.sleep(self.config.collection_interval)
        
        self.logger.info("Collection loop stopped")
    
    def shutdown(self):
        """Shutdown the metrics bridge gracefully."""
        self.logger.info("Shutting down metrics bridge")
        self.running = False
        
        # Shutdown meter provider to flush remaining metrics
        try:
            provider = metrics.get_meter_provider()
            if hasattr(provider, 'shutdown'):
                provider.shutdown()
                self.logger.info("MeterProvider shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    # Load configuration
    config = Config()
    
    # Configure logging
    logging.basicConfig(
        level=config.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting OpenTelemetry Metrics Bridge Sidecar")
    logger.info(str(config))
    
    # Create and run metrics bridge
    bridge = MetricsBridge(config)
    
    try:
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        bridge.shutdown()
        logger.info("Sidecar stopped")


if __name__ == "__main__":
    main()