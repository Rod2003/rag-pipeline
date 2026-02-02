import re
from dataclasses import dataclass
from enum import Enum


class RefusalReason(str, Enum):
    NONE = "none"
    PII = "pii"
    LEGAL_MEDICAL = "legal_medical"


PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN"),  # US SSN
    (r"\b\d{16}\b", "credit card"),  # 16-digit number
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email"),
]

LEGAL_MEDICAL_KEYWORDS = frozenset({
    "legal advice", "lawsuit", "sue", "attorney", "lawyer",
    "medical advice", "diagnose", "prescription", "doctor said",
})


@dataclass
class RefusalResult:
    should_refuse: bool
    reason: RefusalReason
    message: str | None


def check_refusal(query: str) -> RefusalResult:
    """
    check if the query should be refused (PII, legal/medical).
    returns refusal result with should_refuse, reason, and optional message.
    """
    text = query.strip()
    lower = text.lower()

    for pattern, label in PII_PATTERNS:
        if re.search(pattern, text):
            return RefusalResult(
                should_refuse=True,
                reason=RefusalReason.PII,
                message=f"I cannot process queries that appear to contain {label}. Please rephrase without sharing personal information.",
            )

    for kw in LEGAL_MEDICAL_KEYWORDS:
        if kw in lower:
            return RefusalResult(
                should_refuse=True,
                reason=RefusalReason.LEGAL_MEDICAL,
                message="This system provides information from your documents only and does not constitute legal or medical advice. Consult a qualified professional for such matters.",
            )

    return RefusalResult(should_refuse=False, reason=RefusalReason.NONE, message=None)
