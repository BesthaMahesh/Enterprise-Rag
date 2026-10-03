import time
from typing import Dict, Any
from collections import defaultdict


class MetricsCollector:
    """Collects in-memory telemetry, query counts, latency distributions, and cost aggregates."""

    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.latencies: Dict[str, list] = defaultdict(list)
        self.total_tokens_consumed = 0
        self.total_cost_usd = 0.0

    def increment_counter(self, metric_name: str, count: int = 1):
        self.counters[metric_name] += count

    def record_latency(self, metric_name: str, latency_ms: float):
        self.latencies[metric_name].append(latency_ms)
        if len(self.latencies[metric_name]) > 1000:
            self.latencies[metric_name] = self.latencies[metric_name][-1000:]

    def record_tokens_and_cost(self, tokens: int, cost_usd: float):
        self.total_tokens_consumed += tokens
        self.total_cost_usd += cost_usd

    def get_summary(self) -> Dict[str, Any]:
        avg_latencies = {}
        for name, vals in self.latencies.items():
            if vals:
                avg_latencies[name] = round(sum(vals) / len(vals), 2)
        return {
            "counters": dict(self.counters),
            "average_latencies_ms": avg_latencies,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_cost_usd": round(self.total_cost_usd, 6),
        }


metrics_collector = MetricsCollector()
