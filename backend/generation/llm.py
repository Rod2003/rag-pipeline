from mistralai import Mistral
from backend.config import MISTRAL_API_KEY

CHAT_MODEL = "mistral-small-latest"

RAG_PROMPT = """You are a helpful assistant. Use the following context to answer the question. Synthesize and summarize the relevant information from the context. Be concise but thorough.

Only say you don't have enough information if the context is completely irrelevant to the question or empty. If the context is related (even partially), use it to give a helpful answer.

Context:
{context}

Question: {query}

Answer:"""


def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """
    generate an answer using Mistral chat completions with RAG context.
    returns generated answer string.
    """
    if not context_chunks:
        return "I don't have enough information to answer that."

    context = "\n\n---\n\n".join(
        f"[{c.get('source_file', '')} p.{c.get('page', '')}]: {c.get('text', '')}"
        for c in context_chunks
    )

    key = MISTRAL_API_KEY
    if not key:
        raise ValueError("MISTRAL_API_KEY is required for generation")

    client = Mistral(api_key=key)
    response = client.chat.complete(
        model=CHAT_MODEL,
        messages=[
            {"role": "user", "content": RAG_PROMPT.format(context=context, query=query)},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    return content.strip() if content else "I don't have enough information to answer that."
