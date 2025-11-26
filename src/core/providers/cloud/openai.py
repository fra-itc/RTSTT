"""
OpenAI provider implementations for NLP and Summary services.

This module provides OpenAI-powered providers using GPT-4 for:
- NLP analysis (keywords, entities, sentiment)
- Text summarization (summaries, key points, action items)
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any, List
import aiohttp

from ..base import (
    NLPProvider,
    SummaryProvider,
    NLPResult,
    SummaryResult,
    ProviderConfig,
    ProviderCapability,
    ProviderType,
)
from ..exceptions import (
    ProviderAuthenticationError,
    ProviderQuotaExceededError,
    ProviderTimeoutError,
    ProviderResponseError,
)

logger = logging.getLogger(__name__)


class OpenAINLPProvider(NLPProvider):
    """
    OpenAI GPT-4 based NLP provider.

    Uses GPT-4 to extract keywords, entities, sentiment, and topics from text.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_url = config.api_base_url or "https://api.openai.com/v1/chat/completions"
        self.model = config.extra_config.get("model", "gpt-4")
        self.session: Optional[aiohttp.ClientSession] = None

        # Pricing for GPT-4 (per 1K tokens)
        self.input_cost_per_1k = 0.03  # $0.03 per 1K input tokens
        self.output_cost_per_1k = 0.06  # $0.06 per 1K output tokens

    async def initialize(self) -> None:
        """Initialize the OpenAI provider."""
        if not self.config.api_key:
            raise ProviderAuthenticationError(
                "OpenAI API key not configured",
                provider_name=self.name
            )

        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )

        # Test the API key with a simple health check
        try:
            await self.health_check()
            self._is_initialized = True
            logger.info(f"OpenAI NLP provider initialized with model {self.model}")
        except Exception as e:
            self._is_initialized = False
            logger.error(f"Failed to initialize OpenAI NLP provider: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the provider and clean up resources."""
        if self.session:
            await self.session.close()
        self._is_initialized = False
        logger.info("OpenAI NLP provider shutdown")

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        if not self.session:
            return False

        try:
            # Simple test request
            response = await self._make_request(
                "Hello",
                max_tokens=10
            )
            self._is_healthy = True
            return True
        except Exception as e:
            logger.error(f"OpenAI NLP health check failed: {e}")
            self._is_healthy = False
            return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Return list of capabilities."""
        return [
            ProviderCapability.KEYWORD_EXTRACTION,
            ProviderCapability.ENTITY_RECOGNITION,
            ProviderCapability.SENTIMENT_ANALYSIS,
            ProviderCapability.TOPIC_MODELING,
            ProviderCapability.LANGUAGE_DETECTION,
        ]

    async def _make_request(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make a request to OpenAI API with retries."""
        if not self.session:
            raise ProviderResponseError("Provider not initialized", provider_name=self.name)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes text and returns structured JSON responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with self.session.post(self.api_url, json=payload) as response:
                if response.status == 401:
                    raise ProviderAuthenticationError(
                        "Invalid OpenAI API key",
                        provider_name=self.name
                    )
                elif response.status == 429:
                    if retry_count < self.config.max_retries:
                        # Exponential backoff
                        wait_time = 2 ** retry_count
                        logger.warning(f"Rate limited, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(prompt, temperature, max_tokens, retry_count + 1)
                    else:
                        raise ProviderQuotaExceededError(
                            "OpenAI rate limit exceeded",
                            provider_name=self.name
                        )
                elif response.status != 200:
                    error_text = await response.text()
                    raise ProviderResponseError(
                        f"OpenAI API error: {response.status} - {error_text}",
                        provider_name=self.name
                    )

                data = await response.json()
                return data

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(
                "OpenAI API request timed out",
                provider_name=self.name
            )
        except aiohttp.ClientError as e:
            raise ProviderResponseError(
                f"OpenAI API connection error: {str(e)}",
                provider_name=self.name
            )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost

    async def analyze(
        self,
        text: str,
        language: str = "",
        **kwargs
    ) -> NLPResult:
        """
        Analyze text using GPT-4.

        Args:
            text: Input text to analyze
            language: Language code (optional, auto-detected)
            **kwargs: Additional parameters

        Returns:
            NLPResult with analysis
        """
        start_time = time.time()

        # Construct analysis prompt
        prompt = f"""Analyze the following text and provide a structured analysis in JSON format.

Text: "{text}"

Please provide:
1. Keywords: Extract 5-10 important keywords with relevance scores (0-1)
2. Entities: Identify named entities (persons, organizations, locations, dates, etc.)
3. Sentiment: Overall sentiment (positive/negative/neutral) with confidence score
4. Topics: Main topics discussed (3-5 topics)
5. Language: Detected language code (e.g., 'en', 'it', 'es')

Return ONLY a JSON object with this structure:
{{
  "keywords": [{{"word": "example", "score": 0.9, "category": "topic"}}],
  "entities": [{{"text": "John", "type": "PERSON", "confidence": 0.95}}],
  "sentiment": {{"label": "positive", "score": 0.8}},
  "topics": [{{"name": "Business", "confidence": 0.7}}],
  "language": "en"
}}"""

        try:
            response = await self._make_request(prompt, temperature=0.3, max_tokens=1500)

            # Extract response
            message = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Parse JSON response
            try:
                # Clean up response (remove markdown code blocks if present)
                message = message.strip()
                if message.startswith("```"):
                    message = message.split("```")[1]
                    if message.startswith("json"):
                        message = message[4:]
                    message = message.strip()

                analysis = json.loads(message)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response: {message}")
                # Return minimal result
                analysis = {
                    "keywords": [],
                    "entities": [],
                    "sentiment": {"label": "neutral", "score": 0.5},
                    "topics": [],
                    "language": "en"
                }

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Update metrics
            self.update_metrics(
                success=True,
                latency_ms=processing_time,
                cost_usd=cost,
                tokens=total_tokens
            )

            result = NLPResult(
                keywords=analysis.get("keywords", []),
                entities=analysis.get("entities", []),
                sentiment=analysis.get("sentiment", {}),
                topics=analysis.get("topics", []),
                language=analysis.get("language"),
                processing_time_ms=processing_time,
                provider_name=self.name,
                metadata={
                    "model": self.model,
                    "tokens": total_tokens,
                    "cost_usd": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            )

            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.update_metrics(success=False, latency_ms=processing_time)
            logger.error(f"OpenAI NLP analysis failed: {e}")
            raise


class OpenAISummaryProvider(SummaryProvider):
    """
    OpenAI GPT-4 based Summary provider.

    Uses GPT-4 to generate summaries, key points, and action items.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.api_url = config.api_base_url or "https://api.openai.com/v1/chat/completions"
        self.model = config.extra_config.get("model", "gpt-4")
        self.session: Optional[aiohttp.ClientSession] = None

        # Pricing for GPT-4
        self.input_cost_per_1k = 0.03
        self.output_cost_per_1k = 0.06

    async def initialize(self) -> None:
        """Initialize the OpenAI provider."""
        if not self.config.api_key:
            raise ProviderAuthenticationError(
                "OpenAI API key not configured",
                provider_name=self.name
            )

        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )

        self._is_initialized = True
        logger.info(f"OpenAI Summary provider initialized with model {self.model}")

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self.session:
            await self.session.close()
        self._is_initialized = False
        logger.info("OpenAI Summary provider shutdown")

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        if not self.session:
            return False

        try:
            # Simple test
            await self.summarize("Test text", max_length=10, style="concise")
            self._is_healthy = True
            return True
        except Exception as e:
            logger.error(f"OpenAI Summary health check failed: {e}")
            self._is_healthy = False
            return False

    def get_capabilities(self) -> List[ProviderCapability]:
        """Return list of capabilities."""
        return [
            ProviderCapability.EXTRACTIVE_SUMMARY,
            ProviderCapability.ABSTRACTIVE_SUMMARY,
            ProviderCapability.KEY_POINTS,
            ProviderCapability.ACTION_ITEMS,
        ]

    async def _make_request(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 2000,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make a request to OpenAI API."""
        if not self.session:
            raise ProviderResponseError("Provider not initialized", provider_name=self.name)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise, accurate summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with self.session.post(self.api_url, json=payload) as response:
                if response.status == 401:
                    raise ProviderAuthenticationError(
                        "Invalid OpenAI API key",
                        provider_name=self.name
                    )
                elif response.status == 429:
                    if retry_count < self.config.max_retries:
                        wait_time = 2 ** retry_count
                        logger.warning(f"Rate limited, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(prompt, temperature, max_tokens, retry_count + 1)
                    else:
                        raise ProviderQuotaExceededError(
                            "OpenAI rate limit exceeded",
                            provider_name=self.name
                        )
                elif response.status != 200:
                    error_text = await response.text()
                    raise ProviderResponseError(
                        f"OpenAI API error: {response.status} - {error_text}",
                        provider_name=self.name
                    )

                return await response.json()

        except asyncio.TimeoutError:
            raise ProviderTimeoutError(
                "OpenAI API request timed out",
                provider_name=self.name
            )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost

    async def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        style: str = "concise",
        **kwargs
    ) -> SummaryResult:
        """
        Generate summary using GPT-4.

        Args:
            text: Input text to summarize
            max_length: Maximum length in words
            style: Summary style (concise, detailed, bullet_points)
            **kwargs: Additional parameters

        Returns:
            SummaryResult with summary and key points
        """
        start_time = time.time()

        # Construct summary prompt based on style
        style_instructions = {
            "concise": "Create a brief, concise summary in 2-3 sentences.",
            "detailed": "Create a detailed summary covering all main points.",
            "bullet_points": "Create a bullet-point summary with key information.",
        }

        instruction = style_instructions.get(style, style_instructions["concise"])
        length_constraint = f"Maximum length: {max_length} words." if max_length else ""

        prompt = f"""Summarize the following text. {instruction} {length_constraint}

Text: "{text}"

Please provide a structured response in JSON format:
{{
  "summary": "Main summary text",
  "key_points": ["Point 1", "Point 2", "Point 3"],
  "action_items": ["Action 1", "Action 2"],
  "topics": ["Topic 1", "Topic 2"],
  "suggestions": ["Suggestion 1"]
}}

Return ONLY the JSON object."""

        try:
            response = await self._make_request(prompt, temperature=0.5, max_tokens=2000)

            # Extract response
            message = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Parse JSON response
            try:
                # Clean up response
                message = message.strip()
                if message.startswith("```"):
                    message = message.split("```")[1]
                    if message.startswith("json"):
                        message = message[4:]
                    message = message.strip()

                summary_data = json.loads(message)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response: {message}")
                # Use raw message as summary
                summary_data = {
                    "summary": message,
                    "key_points": [],
                    "action_items": [],
                    "topics": [],
                    "suggestions": []
                }

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Update metrics
            self.update_metrics(
                success=True,
                latency_ms=processing_time,
                cost_usd=cost,
                tokens=total_tokens
            )

            result = SummaryResult(
                summary=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points", []),
                action_items=summary_data.get("action_items", []),
                topics=summary_data.get("topics", []),
                suggestions=summary_data.get("suggestions", []),
                confidence=0.9,  # GPT-4 typically high confidence
                processing_time_ms=processing_time,
                provider_name=self.name,
                metadata={
                    "model": self.model,
                    "tokens": total_tokens,
                    "cost_usd": cost,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "style": style,
                }
            )

            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.update_metrics(success=False, latency_ms=processing_time)
            logger.error(f"OpenAI Summary failed: {e}")
            raise
