"""Preparação e recuperação de editais com rastreabilidade."""
import os

# Esta etapa é local: tracing externo exige uma decisão explícita futura.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
