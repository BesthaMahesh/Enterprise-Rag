import re
from typing import Tuple, Dict, Any
from backend.guardrails.prompt_injection import PromptInjectionDetector
from backend.guardrails.pii import PIIDetector
from backend.ingestion.cleaners.text_cleaner import TextCleaner


class InputGuardrail:
    """Processes, classifies, sanitizes, and secures user input before retrieval."""

    @staticmethod
    def classify_query(query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["revenue", "financial", "operating expense", "budget", "cost", "payroll", "salary", "compensation"]):
            if any(w in q for w in ["executive", "incident", "governance", "restricted"]):
                return "RESTRICTED"
            if any(w in q for w in ["hr budget", "workforce", "attrition", "recruitment", "payroll"]):
                return "HR"
            return "FINANCE"
        if any(w in q for w in ["leave", "wfh", "remote", "attendance", "travel", "handbook", "policy", "benefit", "conduct", "learning"]):
            return "POLICY"
        return "GENERAL"

    @staticmethod
    def rewrite_query(query: str) -> str:
        """Expands common HR and business acronyms for enhanced retrieval recall."""
        expanded = query
        expansions = {
            r"\bwfh\b": "work from home remote work",
            r"\bpto\b": "paid time off annual leave",
            r"\bcl\b": "casual leave",
            r"\bsl\b": "sick leave",
            r"\bl&d\b": "learning and development training",
            r"\bopex\b": "operating expense budget",
        }
        for pattern, replacement in expansions.items():
            expanded = re.sub(pattern, replacement, expanded, flags=re.IGNORECASE)
        return expanded

    @staticmethod
    def is_greeting(query: str) -> bool:
        """Identifies standard conversational greetings and assistance inquiries."""
        q = query.strip().lower()
        q_clean = re.sub(r"[^\w\s]", "", q).strip()
        greetings = {
            "hi", "hello", "hey", "hola", "namaste", "good morning", "good afternoon",
            "good evening", "howdy", "greetings", "help", "who are you", "what can you do",
            "what are you", "how are you", "hi there", "hello there", "hey there"
        }
        return q_clean in greetings

    @staticmethod
    def process_input(raw_query: str) -> Dict[str, Any]:
        # Clean & Normalize
        cleaned_query = TextCleaner.clean_text(raw_query)

        # Check prompt injection
        injection_flag, injection_msg = PromptInjectionDetector.detect(cleaned_query)

        # Mask PII in query
        masked_query, pii_findings = PIIDetector.detect_and_mask(cleaned_query)

        # Check if greeting
        is_greeting = InputGuardrail.is_greeting(cleaned_query)

        # Query classification
        query_class = InputGuardrail.classify_query(masked_query)

        # Query rewriting for search
        search_query = InputGuardrail.rewrite_query(masked_query)

        return {
            "original_query": raw_query,
            "cleaned_query": cleaned_query,
            "masked_query": masked_query,
            "search_query": search_query,
            "query_class": query_class,
            "is_greeting": is_greeting,
            "is_injection": injection_flag,
            "injection_reason": injection_msg,
            "pii_findings": pii_findings,
            "is_valid": True
        }
