import re
from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    GENERAL_CHAT = "general_chat"
    KNOWLEDGE_QUERY = "knowledge_query"


GREETINGS = frozenset({ # using frozenset for performance
    "hi", "hello", "hey", "hiya", "howdy", "yo", "sup", "greetings",
    "good morning", "good afternoon", "good evening", "hi there",
})
QUESTION_WORDS = frozenset({"what", "where", "when", "who", "why", "how", "which", "whose"})


def detect_intent(query: str) -> Intent:
    """
    Classify query intent using rule-based heuristics.

    Args:
        query: Raw user input

    Returns:
        Intent: greeting, general_chat, or knowledge_query
    """
    text = query.strip()
    if not text:
        return Intent.GENERAL_CHAT

    lower = text.lower()
    words = set(re.findall(r"\b[a-z]+\b", lower))

    # short greeting-like queries
    if len(text) < 15 and (words & GREETINGS or lower in GREETINGS):
        return Intent.GREETING

    # short queries without question words -> likely casual chat
    if len(text) < 25 and not (words & QUESTION_WORDS):
        # exception: "tell me about X" suggests knowledge query
        if "tell me" in lower or "explain" in lower or "describe" in lower:
            return Intent.KNOWLEDGE_QUERY
        return Intent.GENERAL_CHAT

    # default: treat as factual/knowledge query
    return Intent.KNOWLEDGE_QUERY
