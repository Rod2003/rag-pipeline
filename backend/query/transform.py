import re

# expand common acronyms in domain docs if needed, starting off with these for now
ACRONYM_EXPANSIONS = {
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "nlp": "natural language processing",
    "api": "application programming interface",
    "rag": "retrieval augmented generation",
    "llm": "large language model",
}


def transform_query(query: str) -> str:
    """
    transform query to improve semantic and keyword retrieval.

    - expands known acronyms
    - adds clarifying context for question patterns (e.g. "What is X" -> "definition of X")
    """
    text = query.strip()
    if not text:
        return text

    lower = text.lower()

    # expand acronyms when they appear as standalone tokens
    words = text.split()
    expanded = []
    for w in words:
        clean = re.sub(r"[^a-zA-Z0-9]", "", w).lower()
        if clean in ACRONYM_EXPANSIONS:
            expanded.append(ACRONYM_EXPANSIONS[clean] + " " + w)
        else:
            expanded.append(w)
    text = " ".join(expanded)

    # add clarifying context for definition-style questions
    def_patterns = [
        (r"what\s+is\s+(.+)\?*$", r"definition explanation of \1"),
        (r"what\s+are\s+(.+)\?*$", r"definition explanation of \1"),
        (r"define\s+(.+)$", r"definition of \1"),
        (r"explain\s+(.+)$", r"explanation of \1"),
        (r"how\s+does\s+(.+)\s+work\?*$", r"how \1 works mechanism process"),
        (r"why\s+(.+)\?*$", r"reasons causes for \1"),
    ]
    for pattern, repl in def_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
            break

    return text.strip()
