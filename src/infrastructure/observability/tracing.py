"""OpenTelemetry tracing configuration with OTLP gRPC exporter.

Layer: infrastructure/observability
Call configure_otel() once at application startup before requests are served.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_otel(otlp_endpoint: str, service_name: str = "reservex") -> None:
    """Set up OTLP gRPC span exporter with BatchSpanProcessor."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
