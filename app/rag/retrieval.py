from app.rag.vector_store import get_vector_store
from config import (
    RETRIEVAL_CANDIDATE_MULTIPLIER,
    RETRIEVAL_K,
    RETRIEVAL_MAX_DISTANCE,
)


def retrieve_documents(
    question: str,
    k: int = RETRIEVAL_K,
    max_distance: float = RETRIEVAL_MAX_DISTANCE,
):
    """Return up to k relevant chunks, dropping weak vector matches.

    Chroma returns L2 distance here: smaller is better.
    """
    vector_store = get_vector_store()
    candidate_count = max(k, 1) * max(RETRIEVAL_CANDIDATE_MULTIPLIER, 1)

    candidates = vector_store.similarity_search_with_score(
        question, k=candidate_count
    )

    relevant = [
        doc for doc, distance in candidates if distance <= max_distance
    ]

    return relevant[:k]
