"""
gRPC Server for Summary Service

Provides a gRPC interface for text summarization using Llama-3.2-8B-Instruct model.
Supports single and batch summarization with caching and performance optimization.

Architecture:
    - Wraps SummaryService in a gRPC servicer
    - Provides GenerateSummary RPC for single text summarization
    - Provides GenerateSummaryBatch RPC for batch processing
    - Includes health checks and monitoring
    - Supports concurrent requests with thread pool

Author: Backend ML Services Agent (Track 2)
Date: 2025-11-23
"""

import logging
import time
import traceback
import os
from concurrent import futures
from typing import Optional, Dict, Any, List
import grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

# Proto imports (generated from summary_service.proto)
# Note: Run scripts/generate_proto_stubs.sh to generate these
try:
    from .. import summary_service_pb2
    from .. import summary_service_pb2_grpc
except ImportError:
    # Fallback for development - stubs will be generated during Docker build
    logging.warning("Summary service protobuf stubs not found. Run scripts/generate_proto_stubs.sh")
    summary_service_pb2 = None
    summary_service_pb2_grpc = None

from ..summary_service import SummaryService, SummaryServiceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SummaryServicer:
    """
    gRPC Servicer for Summary operations.

    Implements the SummaryService defined in summary_service.proto.
    Wraps the SummaryService class to provide text summarization via gRPC.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        use_quantization: bool = True,
        use_gpu: bool = True,
        enable_cache: Optional[bool] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize Summary Servicer.

        Args:
            model_name: Llama model name (default: uses SummaryService default)
            use_quantization: Enable 8-bit quantization for memory efficiency
            use_gpu: Use GPU if available
            enable_cache: Enable Redis caching
            redis_host: Redis host override
            redis_port: Redis port override
            **kwargs: Additional arguments for SummaryService
        """
        logger.info("Initializing SummaryServicer...")

        try:
            self.summary_service = SummaryService(
                model_name=model_name,
                use_quantization=use_quantization,
                use_gpu=use_gpu,
                enable_cache=enable_cache,
                redis_host=redis_host,
                redis_port=redis_port
            )
            logger.info("SummaryServicer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SummaryService: {e}")
            logger.error(traceback.format_exc())
            raise

    def GenerateSummary(self, request, context):
        """
        Generate a summary from text.

        Args:
            request: TextRequest containing text and parameters
            context: gRPC context

        Returns:
            SummaryResponse: Generated summary with metadata
        """
        request_id = request.request_id or f"req_{int(time.time() * 1000)}"
        session_id = request.session_id or f"session_{int(time.time() * 1000)}"

        logger.info(f"[{request_id}] Received summarization request")
        logger.info(f"[{request_id}] Session: {session_id}, Text length: {len(request.text)}")

        start_time = time.time()

        try:
            # Validate request
            if not request.text or not request.text.strip():
                logger.error(f"[{request_id}] Empty text provided")
                return self._create_error_response(
                    request_id=request_id,
                    session_id=session_id,
                    error_code=1,
                    error_message="Empty text",
                    error_details="TextRequest.text is empty or whitespace"
                )

            # Extract parameters
            max_length = request.max_length if request.max_length > 0 else None
            min_length = request.min_length if request.min_length > 0 else None
            temperature = request.temperature if request.temperature > 0 else None
            top_p = request.top_p if request.top_p > 0 else None
            use_cache = request.use_cache if request.HasField('use_cache') else True

            # Build metadata from request
            metadata = dict(request.metadata) if request.metadata else {}

            # Generate summary using SummaryService
            logger.info(f"[{request_id}] Generating summary...")

            summary = self.summary_service.generate_summary(
                text=request.text,
                max_length=max_length,
                min_length=min_length,
                temperature=temperature,
                top_p=top_p,
                session_id=session_id,
                metadata=metadata,
                use_cache=use_cache
            )

            # Get cache stats
            cache_stats = self.summary_service.get_cache_stats()

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Check if result was cached (last request was cache hit)
            was_cached = (
                cache_stats['cache_hits'] > 0 and
                processing_time_ms < 50  # Fast response indicates cache hit
            )

            logger.info(f"[{request_id}] Summary generated in {processing_time_ms:.2f}ms")
            logger.info(f"[{request_id}] Summary length: {len(summary)} chars, Cached: {was_cached}")

            # Build gRPC response
            response = summary_service_pb2.SummaryResponse(
                session_id=session_id,
                request_id=request_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                summary=summary,
                text_length=len(request.text),
                summary_length=len(summary),
                confidence=0.95,  # Placeholder - can be enhanced with actual confidence scoring
                compression_ratio=len(summary) / max(len(request.text), 1),
                cached=was_cached,
                processing_time_ms=processing_time_ms,
                status=summary_service_pb2.Status(
                    code=0,
                    message="Success"
                )
            )

            # Add generation parameters
            response.params.CopyFrom(summary_service_pb2.GenerationParams(
                max_length=max_length or self.summary_service.config.DEFAULT_MAX_LENGTH,
                min_length=min_length or self.summary_service.config.DEFAULT_MIN_LENGTH,
                temperature=temperature or self.summary_service.config.DEFAULT_TEMPERATURE,
                top_p=top_p or self.summary_service.config.DEFAULT_TOP_P
            ))

            return response

        except ValueError as e:
            # Input validation error
            logger.error(f"[{request_id}] Validation error: {e}")
            processing_time_ms = (time.time() - start_time) * 1000

            return self._create_error_response(
                request_id=request_id,
                session_id=session_id,
                error_code=1,
                error_message="Validation error",
                error_details=str(e),
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            # Processing error
            logger.error(f"[{request_id}] Summarization failed: {e}")
            logger.error(traceback.format_exc())

            processing_time_ms = (time.time() - start_time) * 1000

            return self._create_error_response(
                request_id=request_id,
                session_id=session_id,
                error_code=2,
                error_message="Summarization failed",
                error_details=str(e),
                processing_time_ms=processing_time_ms
            )

    def GenerateSummaryBatch(self, request, context):
        """
        Generate summaries for multiple texts in batch.

        Args:
            request: BatchTextRequest containing multiple texts
            context: gRPC context

        Returns:
            BatchSummaryResponse: Multiple summaries with metadata
        """
        request_id = request.request_id or f"batch_req_{int(time.time() * 1000)}"
        session_id = request.session_id or f"batch_session_{int(time.time() * 1000)}"

        logger.info(f"[{request_id}] Received batch summarization request")
        logger.info(f"[{request_id}] Session: {session_id}, Batch size: {len(request.texts)}")

        start_time = time.time()

        try:
            # Validate request
            if not request.texts:
                logger.error(f"[{request_id}] Empty text list provided")
                return self._create_batch_error_response(
                    request_id=request_id,
                    session_id=session_id,
                    error_code=1,
                    error_message="Empty batch",
                    error_details="BatchTextRequest.texts is empty"
                )

            # Extract parameters
            max_length = request.max_length if request.max_length > 0 else None
            metadata = dict(request.metadata) if request.metadata else {}

            # Process batch
            logger.info(f"[{request_id}] Processing batch of {len(request.texts)} texts...")

            summaries = self.summary_service.generate_summaries_batch(
                texts=list(request.texts),
                max_length=max_length,
                metadata=metadata
            )

            # Calculate stats
            total_processing_time_ms = (time.time() - start_time) * 1000
            successful_count = sum(1 for s in summaries if s)
            failed_count = len(summaries) - successful_count

            logger.info(f"[{request_id}] Batch completed in {total_processing_time_ms:.2f}ms")
            logger.info(f"[{request_id}] Success: {successful_count}, Failed: {failed_count}")

            # Build batch response
            response = summary_service_pb2.BatchSummaryResponse(
                session_id=session_id,
                request_id=request_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                total_processing_time_ms=total_processing_time_ms,
                successful_count=successful_count,
                failed_count=failed_count,
                status=summary_service_pb2.Status(
                    code=0 if failed_count == 0 else 1,
                    message="Success" if failed_count == 0 else f"{failed_count} summaries failed"
                )
            )

            # Add individual summary responses
            for i, (text, summary) in enumerate(zip(request.texts, summaries)):
                if summary:
                    summary_response = summary_service_pb2.SummaryResponse(
                        session_id=f"{session_id}_item_{i}",
                        request_id=f"{request_id}_item_{i}",
                        timestamp=response.timestamp,
                        summary=summary,
                        text_length=len(text),
                        summary_length=len(summary),
                        compression_ratio=len(summary) / max(len(text), 1),
                        cached=False,
                        processing_time_ms=0.0,  # Per-item timing not tracked in batch
                        status=summary_service_pb2.Status(code=0, message="Success")
                    )
                else:
                    summary_response = summary_service_pb2.SummaryResponse(
                        session_id=f"{session_id}_item_{i}",
                        request_id=f"{request_id}_item_{i}",
                        timestamp=response.timestamp,
                        summary="",
                        text_length=len(text),
                        summary_length=0,
                        status=summary_service_pb2.Status(code=2, message="Failed")
                    )

                response.summaries.append(summary_response)

            return response

        except ValueError as e:
            # Input validation error
            logger.error(f"[{request_id}] Validation error: {e}")
            total_processing_time_ms = (time.time() - start_time) * 1000

            return self._create_batch_error_response(
                request_id=request_id,
                session_id=session_id,
                error_code=1,
                error_message="Validation error",
                error_details=str(e),
                total_processing_time_ms=total_processing_time_ms
            )

        except Exception as e:
            # Processing error
            logger.error(f"[{request_id}] Batch summarization failed: {e}")
            logger.error(traceback.format_exc())

            total_processing_time_ms = (time.time() - start_time) * 1000

            return self._create_batch_error_response(
                request_id=request_id,
                session_id=session_id,
                error_code=2,
                error_message="Batch summarization failed",
                error_details=str(e),
                total_processing_time_ms=total_processing_time_ms
            )

    def HealthCheck(self, request, context):
        """
        Health check for service availability.

        Args:
            request: HealthCheckRequest
            context: gRPC context

        Returns:
            HealthCheckResponse: Service health status
        """
        logger.info("Health check requested")

        try:
            # Get health status from SummaryService
            health_status = self.summary_service.health_check()

            # Determine serving status
            is_serving = health_status['status'] in ['healthy', 'degraded']

            status = (summary_service_pb2.HealthCheckResponse.SERVING
                     if is_serving
                     else summary_service_pb2.HealthCheckResponse.NOT_SERVING)

            # Get model info
            model_info = self.summary_service.summarizer.get_model_info()

            # Get cache stats
            cache_stats = self.summary_service.get_cache_stats()

            response = summary_service_pb2.HealthCheckResponse(
                status=status,
                message=f"Summary service is {health_status['status']}",
                model_info=summary_service_pb2.ModelInfo(
                    name=model_info.get('model_name', 'unknown'),
                    device=model_info.get('device', 'unknown'),
                    model_size_gb=model_info.get('model_size_gb', 0.0),
                    is_loaded=model_info.get('loaded', False),
                    cache_stats=summary_service_pb2.CacheStats(
                        total_cached=cache_stats.get('total_cached', 0),
                        cache_hits=cache_stats.get('cache_hits', 0),
                        cache_misses=cache_stats.get('cache_misses', 0),
                        hit_rate=cache_stats.get('hit_rate', 0.0),
                        cache_enabled=cache_stats.get('cache_enabled', False)
                    )
                )
            )

            logger.info(f"Health check: {response.message}")
            return response

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return summary_service_pb2.HealthCheckResponse(
                status=summary_service_pb2.HealthCheckResponse.NOT_SERVING,
                message=f"Health check error: {str(e)}"
            )

    def _create_error_response(
        self,
        request_id: str,
        session_id: str,
        error_code: int,
        error_message: str,
        error_details: str = "",
        processing_time_ms: float = 0.0
    ):
        """
        Create an error response.

        Args:
            request_id: Request identifier
            session_id: Session identifier
            error_code: Error code (non-zero)
            error_message: Human-readable error message
            error_details: Detailed error information
            processing_time_ms: Processing time before error

        Returns:
            SummaryResponse with error status
        """
        return summary_service_pb2.SummaryResponse(
            session_id=session_id,
            request_id=request_id,
            timestamp="",
            summary="",
            text_length=0,
            summary_length=0,
            processing_time_ms=processing_time_ms,
            status=summary_service_pb2.Status(
                code=error_code,
                message=error_message,
                error_details=error_details
            )
        )

    def _create_batch_error_response(
        self,
        request_id: str,
        session_id: str,
        error_code: int,
        error_message: str,
        error_details: str = "",
        total_processing_time_ms: float = 0.0
    ):
        """
        Create a batch error response.

        Args:
            request_id: Request identifier
            session_id: Session identifier
            error_code: Error code (non-zero)
            error_message: Human-readable error message
            error_details: Detailed error information
            total_processing_time_ms: Processing time before error

        Returns:
            BatchSummaryResponse with error status
        """
        return summary_service_pb2.BatchSummaryResponse(
            session_id=session_id,
            request_id=request_id,
            timestamp="",
            total_processing_time_ms=total_processing_time_ms,
            successful_count=0,
            failed_count=0,
            status=summary_service_pb2.Status(
                code=error_code,
                message=error_message,
                error_details=error_details
            )
        )


def serve(
    port: int = 50053,
    max_workers: int = 10,
    model_name: Optional[str] = None,
    use_quantization: bool = True,
    use_gpu: bool = True,
    enable_cache: Optional[bool] = None,
    redis_host: Optional[str] = None,
    redis_port: Optional[int] = None,
    **kwargs
):
    """
    Start the gRPC server.

    Args:
        port: Port to listen on (default: 50053)
        max_workers: Maximum number of worker threads (default: 10)
        model_name: Llama model name
        use_quantization: Enable 8-bit quantization
        use_gpu: Use GPU if available
        enable_cache: Enable Redis caching
        redis_host: Redis host override
        redis_port: Redis port override
        **kwargs: Additional arguments for SummaryService
    """
    logger.info(f"Starting Summary gRPC server on port {port}...")

    # Create server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 10 * 1024 * 1024),  # 10 MB
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10 MB
        ]
    )

    # Add Summary servicer
    summary_service_pb2_grpc.add_SummaryServiceServicer_to_server(
        SummaryServicer(
            model_name=model_name,
            use_quantization=use_quantization,
            use_gpu=use_gpu,
            enable_cache=enable_cache,
            redis_host=redis_host,
            redis_port=redis_port,
            **kwargs
        ),
        server
    )

    # Add standard gRPC health checking service
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    # Set service as SERVING
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("summary.SummaryService", health_pb2.HealthCheckResponse.SERVING)

    # Bind port and start
    server.add_insecure_port(f'[::]:{port}')
    server.start()

    logger.info(f"gRPC server started successfully on port {port}")
    logger.info(f"Model: {model_name or 'default'}")
    logger.info(f"GPU: {use_gpu}, Quantization: {use_quantization}")
    logger.info(f"Redis: {redis_host or 'localhost'}:{redis_port or 6379}")
    logger.info("Standard gRPC health check enabled")
    logger.info("Server is ready to accept requests...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)
        logger.info("Server stopped")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description="Summary gRPC Server")
    parser.add_argument("--port", type=int, default=50053, help="Port to listen on")
    parser.add_argument("--model", type=str, default=None, help="Llama model name")
    parser.add_argument("--workers", type=int, default=10, help="Max worker threads")
    parser.add_argument("--redis-host", type=str, default=None, help="Redis host")
    parser.add_argument("--redis-port", type=int, default=None, help="Redis port")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU")
    parser.add_argument("--no-quantization", action="store_true", help="Disable quantization")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")

    args = parser.parse_args()

    serve(
        port=args.port,
        max_workers=args.workers,
        model_name=args.model,
        use_quantization=not args.no_quantization,
        use_gpu=not args.no_gpu,
        enable_cache=not args.no_cache,
        redis_host=args.redis_host,
        redis_port=args.redis_port
    )
