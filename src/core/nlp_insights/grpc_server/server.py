"""
gRPC Server for NLP Insights Service

Provides a gRPC interface for NLP insights extraction including keyword extraction,
entity recognition, and sentiment analysis from transcribed text.

Architecture:
    - Wraps NLPService in a gRPC servicer
    - Provides ExtractInsights RPC for synchronous insights extraction
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
from typing import Optional, Dict, Any
import grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

# Proto imports (generated from nlp_service.proto)
# Note: Run scripts/generate_proto_stubs.sh to generate these
try:
    from .. import nlp_service_pb2
    from .. import nlp_service_pb2_grpc
except ImportError:
    # Fallback for development - stubs will be generated during Docker build
    logging.warning("NLP service protobuf stubs not found. Run scripts/generate_proto_stubs.sh")
    nlp_service_pb2 = None
    nlp_service_pb2_grpc = None

from ..nlp_service import NLPService, NLPServiceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NLPInsightsServicer:
    """
    gRPC Servicer for NLP Insights operations.

    Implements the NLPService defined in nlp_service.proto.
    Wraps the NLPService class to provide keyword extraction, entity recognition,
    and sentiment analysis via gRPC.
    """

    def __init__(
        self,
        keyword_model: Optional[str] = None,
        diarization_token: Optional[str] = None,
        enable_diarization: bool = False,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize NLP Insights Servicer.

        Args:
            keyword_model: Model name for keyword extraction
            diarization_token: HuggingFace token for speaker diarization
            enable_diarization: Enable speaker diarization (default: False)
            redis_host: Redis host override
            redis_port: Redis port override
            **kwargs: Additional arguments for NLPService
        """
        logger.info("Initializing NLPInsightsServicer...")

        try:
            self.nlp_service = NLPService(
                keyword_model=keyword_model,
                diarization_token=diarization_token,
                enable_diarization=enable_diarization,
                redis_host=redis_host,
                redis_port=redis_port
            )
            logger.info("NLPInsightsServicer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NLPService: {e}")
            logger.error(traceback.format_exc())
            raise

    def ExtractInsights(self, request, context):
        """
        Extract NLP insights from transcription text.

        Args:
            request: TranscriptionRequest containing text and parameters
            context: gRPC context

        Returns:
            InsightsResponse: Extracted insights with keywords, entities, sentiment
        """
        request_id = request.request_id or f"req_{int(time.time() * 1000)}"
        session_id = request.session_id or f"session_{int(time.time() * 1000)}"

        logger.info(f"[{request_id}] Received insights extraction request")
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
                    error_details="TranscriptionRequest.text is empty or whitespace"
                )

            # Extract insights using NLPService
            logger.info(f"[{request_id}] Processing with NLPService...")

            # Build metadata from request
            metadata = dict(request.metadata) if request.metadata else {}

            # Process transcription
            result = self.nlp_service.process_transcription(
                text=request.text,
                session_id=session_id,
                metadata=metadata
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            logger.info(f"[{request_id}] Processing completed in {processing_time_ms:.2f}ms")
            logger.info(f"[{request_id}] Extracted {len(result['keywords'])} keywords")

            # Build gRPC response
            response = nlp_service_pb2.InsightsResponse(
                session_id=session_id,
                request_id=request_id,
                timestamp=result['timestamp'],
                processing_time_ms=processing_time_ms,
                status=nlp_service_pb2.Status(
                    code=0,
                    message="Success"
                )
            )

            # Add keywords
            for kw_data in result['keywords']:
                keyword = nlp_service_pb2.Keyword(
                    keyword=kw_data['keyword'],
                    score=kw_data['score'],
                    ngram_size=len(kw_data['keyword'].split())
                )
                response.keywords.append(keyword)

            # Add text stats
            stats = result['insights']['text_stats']
            response.text_stats.CopyFrom(nlp_service_pb2.TextStats(
                char_count=stats['char_count'],
                word_count=stats['word_count'],
                sentence_count=stats['sentence_count'],
                avg_word_length=stats['char_count'] / max(stats['word_count'], 1),
                lexical_diversity=0.0  # TODO: Calculate if needed
            ))

            # Note: Entity extraction and sentiment analysis not implemented in current NLPService
            # These can be added in future iterations

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
            logger.error(f"[{request_id}] Processing failed: {e}")
            logger.error(traceback.format_exc())

            processing_time_ms = (time.time() - start_time) * 1000

            return self._create_error_response(
                request_id=request_id,
                session_id=session_id,
                error_code=2,
                error_message="Processing failed",
                error_details=str(e),
                processing_time_ms=processing_time_ms
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
            # Get health status from NLPService
            health_status = self.nlp_service.health_check()

            # Determine serving status
            is_serving = health_status['status'] in ['healthy', 'degraded']

            status = (nlp_service_pb2.HealthCheckResponse.SERVING
                     if is_serving
                     else nlp_service_pb2.HealthCheckResponse.NOT_SERVING)

            # Get model info
            model_info = self.nlp_service.keyword_extractor.get_model_info()

            # Build component statuses
            components = {
                'keyword_extractor': health_status['components'].get('keyword_extractor', 'unknown'),
                'redis': health_status['components'].get('redis', 'unknown')
            }

            response = nlp_service_pb2.HealthCheckResponse(
                status=status,
                message=f"NLP service is {health_status['status']}",
                model_info=nlp_service_pb2.ModelInfo(
                    name=model_info.get('model_name', 'unknown'),
                    device=os.getenv('DEVICE', 'cpu'),
                    is_loaded=True,
                    components=components
                )
            )

            logger.info(f"Health check: {response.message}")
            return response

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return nlp_service_pb2.HealthCheckResponse(
                status=nlp_service_pb2.HealthCheckResponse.NOT_SERVING,
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
            InsightsResponse with error status
        """
        return nlp_service_pb2.InsightsResponse(
            session_id=session_id,
            request_id=request_id,
            timestamp="",
            processing_time_ms=processing_time_ms,
            status=nlp_service_pb2.Status(
                code=error_code,
                message=error_message,
                error_details=error_details
            )
        )


def serve(
    port: int = 50052,
    max_workers: int = 10,
    keyword_model: Optional[str] = None,
    enable_diarization: bool = False,
    redis_host: Optional[str] = None,
    redis_port: Optional[int] = None,
    **kwargs
):
    """
    Start the gRPC server.

    Args:
        port: Port to listen on (default: 50052)
        max_workers: Maximum number of worker threads (default: 10)
        keyword_model: Model name for keyword extraction
        enable_diarization: Enable speaker diarization (default: False)
        redis_host: Redis host override
        redis_port: Redis port override
        **kwargs: Additional arguments for NLPService
    """
    logger.info(f"Starting NLP Insights gRPC server on port {port}...")

    # Create server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 10 * 1024 * 1024),  # 10 MB
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),  # 10 MB
        ]
    )

    # Add NLP Insights servicer
    nlp_service_pb2_grpc.add_NLPServiceServicer_to_server(
        NLPInsightsServicer(
            keyword_model=keyword_model,
            enable_diarization=enable_diarization,
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
    health_servicer.set("nlp.NLPService", health_pb2.HealthCheckResponse.SERVING)

    # Bind port and start
    server.add_insecure_port(f'[::]:{port}')
    server.start()

    logger.info(f"gRPC server started successfully on port {port}")
    logger.info(f"Model: {keyword_model or 'default'}")
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

    parser = argparse.ArgumentParser(description="NLP Insights gRPC Server")
    parser.add_argument("--port", type=int, default=50052, help="Port to listen on")
    parser.add_argument("--model", type=str, default=None, help="Keyword extraction model name")
    parser.add_argument("--workers", type=int, default=10, help="Max worker threads")
    parser.add_argument("--redis-host", type=str, default=None, help="Redis host")
    parser.add_argument("--redis-port", type=int, default=None, help="Redis port")
    parser.add_argument("--enable-diarization", action="store_true", help="Enable speaker diarization")

    args = parser.parse_args()

    serve(
        port=args.port,
        max_workers=args.workers,
        keyword_model=args.model,
        enable_diarization=args.enable_diarization,
        redis_host=args.redis_host,
        redis_port=args.redis_port
    )
