import re
from typing import Tuple, List

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|system)\s+instructions",
    r"ignore\s+(the\s+)?(access\s+rules|acl|permissions|restrictions)",
    r"bypass\s+(the\s+)?(acl|security|policy|restrictions)",
    r"act\s+as\s+(an?\s+)?(hr\s+admin|administrator|system\s+admin|root|superuser)",
    r"you\s+are\s+now\s+(an?\s+)?(administrator|hr\s+officer|ceo|unrestricted|dan)",
    r"reveal\s+(all\s+)?(restricted|confidential|secret|hidden|private)\s+documents",
    r"show\s+me\s+all\s+(confidential|restricted|private|salary|payroll)\s+documents",
    r"override\s+(security|role|permission|system)",
    r"print\s+(the\s+)?(system\s+prompt|context|hidden\s+text)",
    r"disregard\s+(the\s+)?(rules|role|policy)",
    # System Prompt & Internal Instruction Extraction
    r"(?:reveal|show|print|display|tell\s+me|repeat|dump)\s+(?:all\s+)?(?:your\s+)?(?:system\s+prompt|initial\s+prompt|hidden\s+instructions|system\s+instructions|meta\s+prompt|developer\s+message)",
    # Credential Extraction
    r"(?:reveal|show|print|dump|extract)\s+(?:[a-zA-Z]+\s+){0,3}(?:api[_-]?keys?|passwords?|jwt|tokens?|database\s+url|secret\s+key|credentials)",
    # Jailbreaks & Mode Switching
    r"(?:\bdan\b|dan\s+mode|developer\s+mode|jailbreak|do\s+anything\s+now|evil\s+mode|unrestricted\s+mode)",
    r"pretend\s+(?:you\s+have\s+no\s+(?:rules|filters|limitations)|to\s+be\s+an\s+unrestricted)",
    # Indirect Injection / Overrides
    r"(?:new\s+rule|system\s+update|admin\s+override|system\s+override)",
    r"(?:from\s+now\s+on\s+you\s+(?:must|will)\s+(?:ignore|bypass))",
]

COMPILED_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class PromptInjectionDetector:
    """Detects adversarial jailbreak attempts and prompt injection patterns."""

    @staticmethod
    def detect(query: str) -> Tuple[bool, str]:
        if not query:
            return False, ""

        for pattern in COMPILED_INJECTION_REGEX:
            match = pattern.search(query)
            if match:
                return True, f"Suspicious prompt injection pattern detected: '{match.group(0)}'"

        return False, ""
