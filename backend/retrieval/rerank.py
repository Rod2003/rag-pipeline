import numpy as np


def rerank_by_semantic(
    rrf_results: list[tuple[int, float]],
    query_embedding: list[float],
    chunks: list[dict],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """
    re-rank RRF results by semantic similarity to query.
    returns list of (chunk_index, semantic_score) sorted by score descending.
    """
    if not rrf_results or not chunks:
        return []

    query = np.array(query_embedding, dtype=np.float32)
    query_norm = query / (np.linalg.norm(query) + 1e-10)

    scores = []
    for idx, _ in rrf_results:
        if idx >= len(chunks):
            continue
        emb = chunks[idx].get("embedding")
        if emb is None:
            continue
        vec = np.array(emb, dtype=np.float32)
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        score = float(np.dot(query_norm, vec_norm))
        scores.append((idx, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
