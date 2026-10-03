class CostTracker:
    """Calculates operational LLM token cost in USD."""

    # Pricing per 1M tokens
    MODEL_PRICING = {
        "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "default": {"input": 0.50, "output": 0.75}
    }

    @classmethod
    def calculate_cost(cls, model_name: str, input_tokens: int, output_tokens: int) -> float:
        pricing = cls.MODEL_PRICING.get(model_name.lower(), cls.MODEL_PRICING["default"])
        input_cost = (input_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (output_tokens / 1_000_000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)
