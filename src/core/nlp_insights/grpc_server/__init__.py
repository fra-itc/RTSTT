"""
NLP Insights gRPC Server Module

Provides gRPC interface for NLP insights extraction service.
"""

from .server import NLPInsightsServicer, serve

__all__ = ['NLPInsightsServicer', 'serve']
