import abc
import logging
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.llm.prompts import INSUFFICIENT_KNOWLEDGE_FALLBACK

logger = logging.getLogger(__name__)


class LLMProvider(abc.ABC):
    """Abstract interface for LLM backends."""

    @abc.abstractmethod
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 1024) -> str:
        pass


class GroqProvider(LLMProvider):
    """Groq API implementation for ultra-fast Llama-3 / Mixtral inference."""

    def __init__(self, api_key: str = None, model: str = None):
        from groq import Groq
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.client = Groq(api_key=self.api_key, timeout=settings.LLM_TIMEOUT)

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 1024) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            msg = response.choices[0].message
            content = msg.content or ""
            if not content and hasattr(msg, "reasoning") and msg.reasoning:
                content = msg.reasoning
            return content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise e


class OpenAIProvider(LLMProvider):
    """OpenAI API implementation."""

    def __init__(self, api_key: str = None, model: str = None):
        import openai
        self.client = openai.OpenAI(api_key=api_key or settings.LLM_API_KEY)
        self.model = model or "gpt-4o-mini"

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 1024) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for offline testing and fallback."""

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 1024) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        if "Authorized Enterprise Context:" in last_msg:
            # Extract grounded response
            return "Based on the authorized enterprise policy, your request is addressed in accordance with company guidelines."
        return INSUFFICIENT_KNOWLEDGE_FALLBACK
