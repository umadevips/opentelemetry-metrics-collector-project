.PHONY: help dev-up dev-down build-python build-go verify logs-sidecar-python logs-sidecar-go logs-ml logs-collector logs-prometheus clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev-up: ## Start the development environment
	@echo "Starting ML OpenTelemetry Sidecar development environment..."
	docker compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo ""
	@echo "Services available:"
	@echo "  - OpenTelemetry Collector: http://localhost:4317 (OTLP gRPC)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - OTel Collector Metrics: http://localhost:8889/metrics"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Implement your sidecar (Python or Go)"
	@echo "  2. Add your sidecar in docker compose.yml"
	@echo "  3. Build your sidecar: make build-python OR make build-go"
	@echo "  4. Restart services: make dev-down && make dev-up"
	@echo "  5. Verify metrics: make verify"

dev-down: ## Stop the development environment
	@echo "Stopping development environment..."
	docker compose down
	@echo "✓ Services stopped"

build-python: ## Build the Python sidecar image
	@echo "Building Python sidecar Docker image..."
	docker compose build sidecar-python
	@echo "✓ Python sidecar built successfully"

build-go: ## Build the Go sidecar image
	@echo "Building Go sidecar Docker image..."
	docker compose build sidecar-go
	@echo "✓ Go sidecar built successfully"

verify: ## Verify that metrics are flowing to Prometheus
	@echo "Checking if metrics are available..."
	@echo ""
	@echo "=== OpenTelemetry Collector Metrics Endpoint ==="
	@curl -s http://localhost:8889/metrics | grep -E "^ml_metrics_" | head -20 || echo "⚠ No ml_metrics found yet. Make sure your sidecar is running and exporting metrics."
	@echo ""
	@echo "=== Prometheus Targets ==="
	@curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[^"]*"' || echo "⚠ Could not fetch Prometheus targets"
	@echo ""
	@echo "To view metrics in browser:"
	@echo "  - Prometheus UI: http://localhost:9090"
	@echo "  - Query examples:"
	@echo "    * ml_metrics_ml_training_loss"
	@echo "    * ml_metrics_ml_training_accuracy"

logs-sidecar-python: ## View Python sidecar logs
	docker compose logs -f sidecar-python
docker manifest inspect ghcr.io/openteams-ai/mock-ml-job@sha256:ae8db0c63302730daeb7d4493aec2233f13d94b2ccd779fa64a0d86cc402cd88
logs-sidecar-go: ## View Go sidecar logs
	docker compose logs -f sidecar-go

logs-ml: ## View ML training job logs
	docker compose logs -f mock-ml-job

logs-collector: ## View OpenTelemetry collector logs
	docker compose logs -f otel-collector

logs-prometheus: ## View Prometheus logs
	docker compose logs -f prometheus

logs-all: ## View all service logs
	docker compose logs -f

clean: ## Clean up containers, volumes, and images
	@echo "Cleaning up Docker resources..."
	docker compose down -v
	@echo "Removing built images..."
	-docker rmi infra-candidate-challenge-sidecar-python 2>/dev/null || true
	-docker rmi infra-candidate-challenge-sidecar-go 2>/dev/null || true
	-docker rmi infra-candidate-challenge-mock-ml-job 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Kubernetes targets
k8s-deploy: ## Deploy to Kubernetes
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/otel-collector.yaml
	kubectl apply -f k8s/ml-training-job.yaml
	@echo "✓ Deployed to Kubernetes"
	@echo ""
	@echo "Check status with:"
	@echo "  kubectl get pods -n ml-otel-demo"

k8s-delete: ## Delete Kubernetes resources
	@echo "Deleting Kubernetes resources..."
	kubectl delete -f k8s/ml-training-job.yaml --ignore-not-found=true
	kubectl delete -f k8s/otel-collector.yaml --ignore-not-found=true
	kubectl delete -f k8s/namespace.yaml --ignore-not-found=true
	@echo "✓ Kubernetes resources deleted"

k8s-logs-sidecar: ## View sidecar logs in Kubernetes
	@POD=$$(kubectl get pods -n ml-otel-demo -l job-name=ml-training -o jsonpath='{.items[0].metadata.name}'); \
	kubectl logs -n ml-otel-demo $$POD -c sidecar -f

k8s-logs-ml: ## View ML job logs in Kubernetes
	@POD=$$(kubectl get pods -n ml-otel-demo -l job-name=ml-training -o jsonpath='{.items[0].metadata.name}'); \
	kubectl logs -n ml-otel-demo $$POD -c ml-job -f

# Development helpers
test-python: ## Test Python code (if tests exist)
	@echo "Running Python tests..."
	cd sidecar-python && python -m pytest tests/ -v || echo "No tests found"

test-go: ## Test Go code (if tests exist)
	@echo "Running Go tests..."
	cd sidecar-go && go test -v ./... || echo "No tests found"

format-python: ## Format Python code
	@echo "Formatting Python code..."
	cd sidecar-python && black *.py || echo "black not installed"

format-go: ## Format Go code
	@echo "Formatting Go code..."
	cd sidecar-go && go fmt ./...