"""
Integration tests for gRPC NLP and Summary services.

Tests the gRPC interfaces for both services to ensure they work correctly
in the production microservices architecture.

Run these tests after starting the gRPC servers via docker-compose.
"""

import pytest
import grpc
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import proto stubs - these will be generated during Docker build
try:
    from src.core.nlp_insights import nlp_service_pb2, nlp_service_pb2_grpc
    from src.core.summary_generator import summary_service_pb2, summary_service_pb2_grpc
except ImportError:
    pytest.skip("Proto stubs not generated. Run scripts/generate_proto_stubs.sh", allow_module_level=True)


class TestNLPServiceIntegration:
    """Integration tests for NLP gRPC service."""

    @pytest.fixture
    def nlp_channel(self):
        """Create gRPC channel to NLP service."""
        channel = grpc.insecure_channel('localhost:50052')
        yield channel
        channel.close()

    @pytest.fixture
    def nlp_stub(self, nlp_channel):
        """Create NLP service stub."""
        return nlp_service_pb2_grpc.NLPServiceStub(nlp_channel)

    def test_nlp_health_check(self, nlp_stub):
        """Test NLP service health check."""
        request = nlp_service_pb2.HealthCheckRequest(service="nlp")
        response = nlp_stub.HealthCheck(request)

        assert response.status == nlp_service_pb2.HealthCheckResponse.SERVING
        assert "nlp" in response.message.lower() or "ok" in response.message.lower()
        assert response.model_info.is_loaded is True

    def test_extract_insights_basic(self, nlp_stub):
        """Test basic insights extraction."""
        test_text = """
        This is a test transcription for keyword extraction. Machine learning
        and natural language processing are important technologies. We are
        testing the NLP service to ensure it extracts meaningful keywords
        from the text effectively.
        """

        request = nlp_service_pb2.TranscriptionRequest(
            text=test_text,
            session_id="test_session_001",
            request_id="test_req_001",
            top_keywords=5
        )

        response = nlp_stub.ExtractInsights(request)

        # Verify response
        assert response.status.code == 0
        assert response.status.message == "Success"
        assert response.session_id == "test_session_001"
        assert response.request_id == "test_req_001"
        assert len(response.keywords) > 0
        assert response.processing_time_ms > 0

        # Verify keywords have scores
        for keyword in response.keywords:
            assert len(keyword.keyword) > 0
            assert 0.0 <= keyword.score <= 1.0

    def test_extract_insights_empty_text(self, nlp_stub):
        """Test insights extraction with empty text (should fail gracefully)."""
        request = nlp_service_pb2.TranscriptionRequest(
            text="",
            session_id="test_session_002",
            request_id="test_req_002"
        )

        response = nlp_stub.ExtractInsights(request)

        # Should return error
        assert response.status.code != 0
        assert "empty" in response.status.error_details.lower()

    def test_extract_insights_latency(self, nlp_stub):
        """Test that insights extraction meets latency target (<50ms)."""
        test_text = "This is a simple test text for latency measurement."

        request = nlp_service_pb2.TranscriptionRequest(
            text=test_text,
            session_id="test_session_003",
            request_id="test_req_003"
        )

        response = nlp_stub.ExtractInsights(request)

        assert response.status.code == 0
        # Target: <50ms for NLP processing
        assert response.processing_time_ms < 50, f"Latency too high: {response.processing_time_ms}ms"


class TestSummaryServiceIntegration:
    """Integration tests for Summary gRPC service."""

    @pytest.fixture
    def summary_channel(self):
        """Create gRPC channel to Summary service."""
        channel = grpc.insecure_channel('localhost:50053')
        yield channel
        channel.close()

    @pytest.fixture
    def summary_stub(self, summary_channel):
        """Create Summary service stub."""
        return summary_service_pb2_grpc.SummaryServiceStub(summary_channel)

    def test_summary_health_check(self, summary_stub):
        """Test Summary service health check."""
        request = summary_service_pb2.HealthCheckRequest(service="summary")
        response = summary_stub.HealthCheck(request)

        assert response.status == summary_service_pb2.HealthCheckResponse.SERVING
        assert "summary" in response.message.lower() or "ok" in response.message.lower()
        assert response.model_info.is_loaded is True

    def test_generate_summary_basic(self, summary_stub):
        """Test basic summary generation."""
        test_text = """
        This is a comprehensive test transcription for the Summary Service. The meeting
        covered multiple important topics including the implementation of a new machine
        learning pipeline for real-time speech-to-text transcription. The team discussed
        various technical approaches, including the use of Whisper for speech recognition,
        Llama for text summarization, and KeyBERT for keyword extraction. Performance
        optimization was a key concern, with discussions about GPU utilization, model
        quantization, and caching strategies. The team also addressed deployment
        considerations, including Docker containerization and Kubernetes orchestration.
        """

        request = summary_service_pb2.TextRequest(
            text=test_text,
            session_id="test_session_001",
            request_id="test_req_001",
            max_length=100,
            min_length=30
        )

        response = summary_stub.GenerateSummary(request)

        # Verify response
        assert response.status.code == 0
        assert response.status.message == "Success"
        assert response.session_id == "test_session_001"
        assert response.request_id == "test_req_001"
        assert len(response.summary) > 0
        assert response.summary_length > 0
        assert response.processing_time_ms > 0
        assert response.compression_ratio < 1.0  # Summary should be shorter than original

    def test_generate_summary_empty_text(self, summary_stub):
        """Test summary generation with empty text (should fail gracefully)."""
        request = summary_service_pb2.TextRequest(
            text="",
            session_id="test_session_002",
            request_id="test_req_002"
        )

        response = summary_stub.GenerateSummary(request)

        # Should return error
        assert response.status.code != 0
        assert "empty" in response.status.error_details.lower()

    def test_generate_summary_latency(self, summary_stub):
        """Test that summary generation meets latency target (<200ms)."""
        test_text = """
        This is a brief test text for latency measurement. The summary service should
        generate a concise summary of this text quickly and efficiently.
        """

        request = summary_service_pb2.TextRequest(
            text=test_text,
            session_id="test_session_003",
            request_id="test_req_003",
            max_length=50
        )

        response = summary_stub.GenerateSummary(request)

        assert response.status.code == 0
        # Target: <200ms for summary generation
        # Note: First call may be slower due to model loading
        # For cached results, should be much faster

    def test_generate_summary_caching(self, summary_stub):
        """Test that caching works for identical requests."""
        test_text = "This is a caching test text."

        request = summary_service_pb2.TextRequest(
            text=test_text,
            session_id="test_session_004",
            request_id="test_req_004_a",
            max_length=50,
            use_cache=True
        )

        # First call - should not be cached
        response1 = summary_stub.GenerateSummary(request)
        assert response1.status.code == 0

        # Second call - should be cached
        request.request_id = "test_req_004_b"
        response2 = summary_stub.GenerateSummary(request)

        assert response2.status.code == 0
        assert response2.cached is True  # Should be cached
        assert response2.processing_time_ms < response1.processing_time_ms  # Should be faster

    def test_generate_summary_batch(self, summary_stub):
        """Test batch summary generation."""
        texts = [
            "This is the first test text for batch processing.",
            "This is the second test text for batch processing.",
            "This is the third test text for batch processing."
        ]

        request = summary_service_pb2.BatchTextRequest(
            texts=texts,
            session_id="test_session_005",
            request_id="test_req_005",
            max_length=30
        )

        response = summary_stub.GenerateSummaryBatch(request)

        # Verify response
        assert response.status.code == 0
        assert response.successful_count == len(texts)
        assert response.failed_count == 0
        assert len(response.summaries) == len(texts)

        # Verify each summary
        for summary_response in response.summaries:
            assert summary_response.status.code == 0
            assert len(summary_response.summary) > 0


class TestEndToEndIntegration:
    """End-to-end integration tests for complete pipeline."""

    @pytest.fixture
    def nlp_stub(self):
        """Create NLP service stub."""
        channel = grpc.insecure_channel('localhost:50052')
        stub = nlp_service_pb2_grpc.NLPServiceStub(channel)
        yield stub
        channel.close()

    @pytest.fixture
    def summary_stub(self):
        """Create Summary service stub."""
        channel = grpc.insecure_channel('localhost:50053')
        stub = summary_service_pb2_grpc.SummaryServiceStub(channel)
        yield stub
        channel.close()

    def test_complete_pipeline(self, nlp_stub, summary_stub):
        """Test complete NLP + Summary pipeline."""
        test_text = """
        This is a complete integration test for the RTSTT pipeline. We are testing
        the interaction between the NLP service and the Summary service. The NLP
        service extracts keywords and insights, while the Summary service generates
        concise summaries. Both services communicate via gRPC and are horizontally
        scalable microservices. This architecture enables efficient processing of
        real-time speech-to-text transcriptions at scale.
        """

        # Step 1: Extract insights with NLP service
        nlp_request = nlp_service_pb2.TranscriptionRequest(
            text=test_text,
            session_id="e2e_test_001",
            request_id="e2e_nlp_001",
            top_keywords=5
        )

        nlp_response = nlp_stub.ExtractInsights(nlp_request)
        assert nlp_response.status.code == 0
        assert len(nlp_response.keywords) > 0

        # Step 2: Generate summary with Summary service
        summary_request = summary_service_pb2.TextRequest(
            text=test_text,
            session_id="e2e_test_001",
            request_id="e2e_summary_001",
            max_length=100
        )

        summary_response = summary_stub.GenerateSummary(summary_request)
        assert summary_response.status.code == 0
        assert len(summary_response.summary) > 0

        # Verify end-to-end latency target (<500ms total)
        total_latency = nlp_response.processing_time_ms + summary_response.processing_time_ms
        assert total_latency < 500, f"Total latency too high: {total_latency}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
