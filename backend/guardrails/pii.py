import re
from typing import Tuple, List, Dict, Optional
from backend.config.settings import settings

# Core Regex Patterns for Sensitive Enterprise & Personal Identifiers
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
BANK_ACCOUNT_REGEX = re.compile(r"\b(?:acct?|account|a/c)[\s#:]*([0-9]{9,18})\b", re.IGNORECASE)
EMPLOYEE_ID_REGEX = re.compile(r"\b(?:EMP|EMPID|EID)[-_]?[0-9]{3,7}\b", re.IGNORECASE)

# Credential Scrubbing (JWT, API keys)
CREDENTIAL_REGEX = re.compile(r"\b(?:ey[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9_-]{24,}|sk-[A-Za-z0-9_-]{24,})\b")


class PIIDetector:
    """
    Configurable PII detection and masking service for Enterprise compliance.
    Protects user queries, LLM context, answers, and audit records.
    """

    DEFAULT_POLICY: Dict[str, bool] = {
        "email": True,
        "phone": True,
        "pan": True,
        "aadhaar": True,
        "credit_card": True,
        "ssn": True,
        "bank_account": True,
        "employee_id": True,
        "credentials": True,
    }

    @classmethod
    def get_effective_policy(cls, override_policy: Optional[Dict[str, bool]] = None) -> Dict[str, bool]:
        policy = cls.DEFAULT_POLICY.copy()
        if hasattr(settings, "PII_MASK_EMAILS"):
            policy["email"] = settings.PII_MASK_EMAILS
        if override_policy:
            policy.update(override_policy)
        return policy

    @classmethod
    def detect_and_mask(
        cls,
        text: str,
        mask_emails: Optional[bool] = None,
        policy: Optional[Dict[str, bool]] = None
    ) -> Tuple[str, List[str]]:
        if not text:
            return "", []

        effective_policy = cls.get_effective_policy(policy)
        if mask_emails is not None:
            effective_policy["email"] = mask_emails

        findings: List[str] = []
        masked_text = text

        # 1. Credentials (JWT, API Keys)
        if effective_policy.get("credentials", True) and CREDENTIAL_REGEX.search(masked_text):
            findings.append("CREDENTIAL")
            masked_text = CREDENTIAL_REGEX.sub("[REDACTED_CREDENTIAL]", masked_text)

        # 2. Credit Cards
        if effective_policy.get("credit_card", True) and CREDIT_CARD_REGEX.search(masked_text):
            findings.append("CREDIT_CARD")
            masked_text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", masked_text)

        # 3. SSN
        if effective_policy.get("ssn", True) and SSN_REGEX.search(masked_text):
            findings.append("SSN")
            masked_text = SSN_REGEX.sub("[REDACTED_SSN]", masked_text)

        # 4. PAN (India Tax ID)
        if effective_policy.get("pan", True) and PAN_REGEX.search(masked_text):
            findings.append("PAN")
            masked_text = PAN_REGEX.sub("[REDACTED_PAN]", masked_text)

        # 5. Aadhaar (India National ID)
        if effective_policy.get("aadhaar", True) and AADHAAR_REGEX.search(masked_text):
            findings.append("AADHAAR")
            masked_text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", masked_text)

        # 6. Bank Account
        if effective_policy.get("bank_account", True) and BANK_ACCOUNT_REGEX.search(masked_text):
            findings.append("BANK_ACCOUNT")
            masked_text = BANK_ACCOUNT_REGEX.sub(r"account [REDACTED_ACCOUNT]", masked_text)

        # 7. Employee ID
        if effective_policy.get("employee_id", True) and EMPLOYEE_ID_REGEX.search(masked_text):
            findings.append("EMPLOYEE_ID")
            masked_text = EMPLOYEE_ID_REGEX.sub("[REDACTED_EMPLOYEE_ID]", masked_text)

        # 8. Email
        if effective_policy.get("email", True) and EMAIL_REGEX.search(masked_text):
            findings.append("EMAIL")
            masked_text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", masked_text)

        # 9. Phone Number
        if effective_policy.get("phone", True) and PHONE_REGEX.search(masked_text):
            findings.append("PHONE_NUMBER")
            masked_text = PHONE_REGEX.sub("[REDACTED_PHONE]", masked_text)

        return masked_text, list(dict.fromkeys(findings))

    @classmethod
    def sanitize_for_logging(cls, text: str) -> str:
        """Sanitizes text for safe persistence in logs and audit tables without credentials or PII."""
        if not text:
            return ""
        sanitized, _ = cls.detect_and_mask(text)
        return sanitized

