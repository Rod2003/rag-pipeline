RRF_K = 60


def rrf_merge(
    semantic_results: list[tuple[int, float]],
    keyword_results: list[tuple[int, float]],
    k: int = RRF_K,
    top_k: int = 20,
) -> list[tuple[int, float]]:
    """
    merge semantic and keyword rankings using reciprocal rank fusion.

    returns list of (chunk_index, rrf_score) sorted by rrf_score descending.
    """
    scores: dict[int, float] = {}

    for rank, (idx, _) in enumerate(semantic_results, start=1):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)

    for rank, (idx, _) in enumerate(keyword_results, start=1):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)

    merged = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return merged[:top_k]


def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    chunks: list[dict],
    keyword_index=None,
    top_k: int = 20,
):
    """
    combine semantic and keyword search via RRF.
    returns list of (chunk_index, rrf_score), updated BM25Index for reuse.
    """
    from .semantic import semantic_search
    from .keyword import keyword_search

    semantic_results = semantic_search(query_embedding, chunks, top_k=top_k)
    keyword_results, keyword_index = keyword_search(
        query_text, chunks, index=keyword_index, top_k=top_k
    )

    merged = rrf_merge(semantic_results, keyword_results, top_k=top_k)
    return merged, keyword_index
