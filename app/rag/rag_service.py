from app.rag.vector_store import get_vector_store
from app.rag.generation import generate_answer


def ask_question(question: str):
    vector_store = get_vector_store()

    documents = vector_store.similarity_search(
        question,
        k=4
    )

    if not documents:
        return {
            "answer": "Не удалось найти информацию в базе знаний.",
            "sources": []
        }

    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    answer = generate_answer(question, context)

    sources = []

    for doc in documents:
        sources.append({
            "document_id": doc.metadata.get("document_id"),
            "department": doc.metadata.get("department"),
            "document_title": doc.metadata.get("document_title")
        })

    return {
        "answer": answer,
        "sources": sources
    }
