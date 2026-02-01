import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """lowercase and tokenize on non-alphanumeric characters."""
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]+\b", text)
    return tokens


class BM25Index:
    """bm25 index built from chunk texts."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_tokens: list[list[str]] = []
        self.doc_len: list[int] = []
        self.avgdl: float = 0.0
        self.doc_freq: dict[str, int] = {}
        self.N: int = 0

    def build(self, chunks: list[dict]) -> None:
        """build index from chunk texts."""
        self.doc_tokens = [_tokenize(c.get("text", "")) for c in chunks]
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.N = len(chunks)
        self.avgdl = sum(self.doc_len) / self.N if self.N else 0

        # document frequency: number of docs containing each term
        self.doc_freq = {}
        for tokens in self.doc_tokens:
            seen = set()
            for t in tokens:
                if t not in seen:
                    seen.add(t)
                    self.doc_freq[t] = self.doc_freq.get(t, 0) + 1

    def _idf(self, term: str) -> float:
        """IDF component."""
        df = self.doc_freq.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        """BM25 score for a single document."""
        if doc_idx >= len(self.doc_tokens):
            return 0.0
        tokens = self.doc_tokens[doc_idx]
        dl = self.doc_len[doc_idx]
        tf = Counter(tokens)

        total = 0.0
        for term in set(query_tokens):
            if term not in tf:
                continue
            idf = self._idf(term)
            f = tf[term]
            norm = 1 - self.b + self.b * dl / (self.avgdl + 1e-10)
            total += idf * (f * (self.k1 + 1)) / (f + self.k1 * norm)
        return total

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        """
        return top-k documents by bm25 score.
        """
        if not self.doc_tokens:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        scores = [(i, self.score(q_tokens, i)) for i in range(self.N)]
        scores = [(i, s) for i, s in scores if s > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def keyword_search(
    query: str,
    chunks: list[dict],
    index: BM25Index | None = None,
    top_k: int = 20,
) -> tuple[list[tuple[int, float]], BM25Index | None]:
    """
    bm25 search over chunks. builds index if not provided.
    """
    if index is None:
        index = BM25Index()
        index.build(chunks)
    results = index.search(query, top_k=top_k)
    return results, index
