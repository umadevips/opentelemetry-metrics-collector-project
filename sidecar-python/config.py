"""
Configuration management for the metrics bridge.

Loads configuration from environment variables with validation and sensible defaults.
Supports all required configuration parameters for OpenTelemetry integration.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OpenTelemetry Collector gRPC endpoint
        Default: "http://localhost:4317"
        
    OTEL_SERVICE_NAME: Service identifier for telemetry
        Default: "ml-metrics-bridge"
        
    METRICS_FILE_PATH: Path to JSON metrics file
        Default: "/shared/metrics/current.json"
        
    COLLECTION_INTERVAL: Polling frequency in seconds (minimum: 1)
        Default: "10"
        
    LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        Default: "INFO"
"""

import os
import logging
from typing import Optional


class Config:
    """Configuration for the OpenTelemetry metrics bridge."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # OpenTelemetry configuration
        self.otel_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:4317"
        )
        self.service_name = os.getenv(
            "OTEL_SERVICE_NAME",
            "ml-metrics-bridge"
        )
        
        # Metrics file configuration
        self.metrics_file_path = os.getenv(
            "METRICS_FILE_PATH",
            "/shared/metrics/current.json"
        )
        
        # Collection interval in seconds
        self.collection_interval = self._parse_int(
            os.getenv("COLLECTION_INTERVAL", "10"),
            default=10,
            min_value=1
        )
        
        # Logging configuration
        self.log_level = self._parse_log_level(
            os.getenv("LOG_LEVEL", "INFO")
        )
        
        # Validate configuration
        self._validate()
    
    def _parse_int(self, value: str, default: int, min_value: Optional[int] = None) -> int:
        """Parse integer with validation."""
        try:
            parsed = int(value)
            if min_value is not None and parsed < min_value:
                logging.warning(
                    f"Value {parsed} is less than minimum {min_value}, using {default}"
                )
                return default
            return parsed
        except ValueError:
            logging.warning(f"Invalid integer value '{value}', using default {default}")
            return default
    
    def _parse_log_level(self, level: str) -> int:
        """Parse log level string to logging constant."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level.upper(), logging.INFO)
    
    def _validate(self):
        """Validate configuration values."""
        if not self.otel_endpoint:
            raise ValueError("OTEL_EXPORTER_OTLP_ENDPOINT cannot be empty")
        
        if not self.service_name:
            raise ValueError("OTEL_SERVICE_NAME cannot be empty")
        
        if not self.metrics_file_path:
            raise ValueError("METRICS_FILE_PATH cannot be empty")
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config("
            f"otel_endpoint={self.otel_endpoint}, "
            f"service_name={self.service_name}, "
            f"metrics_file_path={self.metrics_file_path}, "
            f"collection_interval={self.collection_interval}s, "
            f"log_level={logging.getLevelName(self.log_level)})"
        )