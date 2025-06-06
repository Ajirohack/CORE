"""
Metrics collection and monitoring for the Archivist system.
Integrates with Prometheus and existing monitoring setup.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import time

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, push_to_gateway

class MetricsCollector:
    def __init__(self, app_name: str = "archivist", push_gateway: str = "localhost:9091"):
        self.registry = CollectorRegistry()
        self.app_name = app_name
        self.push_gateway = push_gateway
        
        # Memory metrics
        self.memory_operations = Counter(
            "memory_operations_total",
            "Total number of memory operations",
            ["operation", "memory_type"],
            registry=self.registry
        )
        
        self.memory_operation_duration = Histogram(
            "memory_operation_duration_seconds",
            "Duration of memory operations",
            ["operation", "memory_type"],
            registry=self.registry
        )
        
        self.active_memories = Gauge(
            "active_memories",
            "Number of active memories",
            ["memory_type"],
            registry=self.registry
        )
        
        # Reasoning metrics
        self.reasoning_operations = Counter(
            "reasoning_operations_total",
            "Total number of reasoning operations",
            ["operation_type"],
            registry=self.registry
        )
        
        self.reasoning_confidence = Histogram(
            "reasoning_confidence",
            "Confidence scores for reasoning operations",
            ["operation_type"],
            registry=self.registry
        )
        
        # Event metrics
        self.events_processed = Counter(
            "events_processed_total",
            "Total number of events processed",
            ["event_type"],
            registry=self.registry
        )
        
        self.event_processing_duration = Histogram(
            "event_processing_duration_seconds",
            "Duration of event processing",
            ["event_type"],
            registry=self.registry
        )
        
        # Storage metrics
        self.storage_operations = Counter(
            "storage_operations_total",
            "Total number of storage operations",
            ["operation", "store_type"],
            registry=self.registry
        )
        
        self.storage_latency = Histogram(
            "storage_latency_seconds",
            "Latency of storage operations",
            ["operation", "store_type"],
            registry=self.registry
        )
        
    def record_memory_operation(self, operation: str, memory_type: str):
        """Record a memory operation"""
        self.memory_operations.labels(operation=operation, memory_type=memory_type).inc()
        
    def time_memory_operation(self, operation: str, memory_type: str):
        """Context manager to time memory operations"""
        return self.memory_operation_duration.labels(
            operation=operation,
            memory_type=memory_type
        ).time()
        
    def update_active_memories(self, count: int, memory_type: str):
        """Update gauge of active memories"""
        self.active_memories.labels(memory_type=memory_type).set(count)
        
    def record_reasoning_operation(self, operation_type: str, confidence: float):
        """Record a reasoning operation with confidence"""
        self.reasoning_operations.labels(operation_type=operation_type).inc()
        self.reasoning_confidence.labels(operation_type=operation_type).observe(confidence)
        
    def record_event(self, event_type: str):
        """Record an event being processed"""
        self.events_processed.labels(event_type=event_type).inc()
        
    def time_event_processing(self, event_type: str):
        """Context manager to time event processing"""
        return self.event_processing_duration.labels(event_type=event_type).time()
        
    def record_storage_operation(self, operation: str, store_type: str):
        """Record a storage operation"""
        self.storage_operations.labels(
            operation=operation,
            store_type=store_type
        ).inc()
        
    def time_storage_operation(self, operation: str, store_type: str):
        """Context manager to time storage operations"""
        return self.storage_latency.labels(
            operation=operation,
            store_type=store_type
        ).time()
        
    def push_metrics(self):
        """Push metrics to Prometheus gateway"""
        try:
            push_to_gateway(
                self.push_gateway,
                job=self.app_name,
                registry=self.registry
            )
        except Exception as e:
            print(f"Error pushing metrics: {e}")

# Global metrics collector instance
collector = MetricsCollector()
