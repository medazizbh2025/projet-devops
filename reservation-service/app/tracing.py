from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import os

def init_tracer(app):
    resource = Resource(attributes={
        "service.name": "reservation-service"
    })
    
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)

    # Configure the OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrument Flask
    FlaskInstrumentor().instrument_app(app)

    return tracer

def inject_trace_info(carrier):
    """Inject trace context into carrier (e.g., Kafka message headers)"""
    TraceContextTextMapPropagator().inject(carrier)

def extract_trace_info(carrier):
    """Extract trace context from carrier (e.g., Kafka message headers)"""
    context = TraceContextTextMapPropagator().extract(carrier)
    return context