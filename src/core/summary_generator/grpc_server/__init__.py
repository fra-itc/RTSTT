"""
Summary gRPC Server Module

Provides gRPC interface for text summarization service.
"""

from .server import SummaryServicer, serve

__all__ = ['SummaryServicer', 'serve']
