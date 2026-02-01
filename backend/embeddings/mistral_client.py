from mistralai import Mistral

from backend.config import MISTRAL_API_KEY

EMBED_MODEL = "mistral-embed"
_BATCH_SIZE = 32  # mistral supports batch; limit for API reliability


def embed_texts(texts: list[str], api_key: str | None = None) -> list[list[float]]:
    """
    embed a list of texts using mistral embeddings API.
    """
    if not texts:
        return []

    key = api_key or MISTRAL_API_KEY
    if not key:
        raise ValueError("MISTRAL_API_KEY is required for embeddings")

    client = Mistral(api_key=key)
    embeddings: list[list[float]] = []

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, inputs=batch)
        for item in sorted(response.data, key=lambda x: x.index):
            embeddings.append(item.embedding)

    return embeddings
