from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.exceptions import EmbeddingServiceException


client = AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_embedding(text: str) -> list[float]:
    try:
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception:
        raise EmbeddingServiceException()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
    magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


async def find_similar_contexts(
    query: str,
    stored_embeddings: list[tuple[str, list[float]]],
    threshold: float = 0.75,
    top_k: int = 5
) -> list[str]:
    query_embedding = await generate_embedding(query)
    scores = []
    for context_id, embedding in stored_embeddings:
        score = cosine_similarity(query_embedding, embedding)
        if score >= threshold:
            scores.append((context_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [context_id for context_id, _ in scores[:top_k]]