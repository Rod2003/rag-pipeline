import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """cosine similarity between two vectors."""
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a_norm, b_norm))


def semantic_search(
    query_embedding: list[float],
    chunks: list[dict],
    top_k: int = 20,
) -> list[tuple[int, float]]:
    """find top-k chunks by cosine similarity to query embedding."""
    if not chunks:
        return []

    query = np.array(query_embedding, dtype=np.float32)
    query_norm = query / (np.linalg.norm(query) + 1e-10)

    scores = []
    for i, chunk in enumerate(chunks):
        emb = chunk.get("embedding")
        if emb is None:
            continue
        vec = np.array(emb, dtype=np.float32)
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        score = float(np.dot(query_norm, vec_norm))
        scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
