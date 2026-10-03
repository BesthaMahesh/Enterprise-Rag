import time
import logging
from typing import List, Dict, Any, Tuple
from backend.config.settings import settings
from backend.llm.provider import LLMProvider, GroqProvider, OpenAIProvider, MockLLMProvider
from backend.reliability.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException, retry_with_backoff

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Robust LLM client orchestrating multi-provider execution, retries,
    circuit breaker protection, and token estimation.
    """

    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            recovery_timeout=settings.CIRCUIT_BREAKER_RECOVERY_TIME
        )
        self.primary_provider = self._init_provider(settings.LLM_PROVIDER)
        self.fallback_provider = MockLLMProvider()

    def _init_provider(self, provider_name: str) -> LLMProvider:
        p = provider_name.lower().strip()
        if p == "groq" and settings.LLM_API_KEY:
            try:
                return GroqProvider(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
            except Exception as e:
                logger.error(f"Failed to initialize GroqProvider: {e}")
        elif p == "openai" and settings.LLM_API_KEY:
            try:
                return OpenAIProvider(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAIProvider: {e}")

        logger.info("Using MockLLMProvider fallback.")
        return MockLLMProvider()

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> Tuple[str, float, int]:
        """
        Generate response with latency tracking and reliability controls.
        Returns: (response_text, latency_ms, estimated_tokens)
        """
        start_time = time.perf_counter()

        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker OPEN. Routing to mock fallback.")
            res = self.fallback_provider.generate(messages, temperature=temperature, max_tokens=max_tokens)
            latency_ms = (time.perf_counter() - start_time) * 1000
            return res, latency_ms, len(res.split())

        try:
            res = self._call_provider_with_retry(messages, temperature, max_tokens)
            self.circuit_breaker.record_success()
            latency_ms = (time.perf_counter() - start_time) * 1000
            toks = len(res.split()) * 4 // 3
            return res, latency_ms, toks
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Primary LLM generation failed: {e}. Executing fallback.")
            res = self.fallback_provider.generate(messages, temperature=temperature, max_tokens=max_tokens)
            latency_ms = (time.perf_counter() - start_time) * 1000
            return res, latency_ms, len(res.split())

    @retry_with_backoff(retries=3, initial_delay=0.5, backoff_factor=2.0)
    def _call_provider_with_retry(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        return self.primary_provider.generate(messages, temperature=temperature, max_tokens=max_tokens)


llm_client = LLMClient()
