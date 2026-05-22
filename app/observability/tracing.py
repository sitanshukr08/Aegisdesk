import os
from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from openinference.instrumentation.langchain import LangChainInstrumentor

def setup_tracing(app: FastAPI):
    """
    Initializes OpenTelemetry distributed tracing for FastAPI and LangGraph.
    Only enables tracing if OTEL_EXPORTER_OTLP_ENDPOINT is set in the environment.
    """
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    if not otlp_endpoint:
        # If no endpoint is configured (e.g. local CLI use), skip tracing setup
        return

    # Define the Service Resource
    resource = Resource.create(
        attributes={
            "service.name": "aegisdesk-api",
            "service.version": "0.1.1"
        }
    )

    # Set up the Tracer Provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure the OTLP Exporter (gRPC)
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument LangChain & LangGraph (captures nodes, tools, and prompts)
    LangChainInstrumentor().instrument()

    # We also have chromadb instrumentation if we installed opentelemetry-instrumentation-chromadb,
    # but openinference usually catches the vector ops natively via LangChain.
