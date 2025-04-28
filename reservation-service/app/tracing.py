from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
import os

def init_tracer(app, service_name="reservation-service"):
    # Configure the tracer
    resource = Resource(attributes={
        "service.name": service_name,
        "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development")
    })
    
    # Create and set tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTLP_ENDPOINT", "http://jaeger:4317"),
        insecure=True
    )
    
    # Add span processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Instrument Flask
    FlaskInstrumentor().instrument_app(app)
    
    # Instrument Kafka
    KafkaInstrumentor().instrument()
    
    return trace.get_tracer(__name__)

def create_span(name, parent_ctx=None):
    """Create a new span with optional parent context"""
    tracer = trace.get_tracer(__name__)
    if parent_ctx:
        return tracer.start_span(name, context=parent_ctx)
    return tracer.start_span(name)

def inject_trace_headers(headers):
    """Inject trace context into message headers for distributed tracing"""
    from opentelemetry.propagate import inject
    inject(headers)