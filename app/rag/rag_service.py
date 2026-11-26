from app.rag.generation import generate_answer
from app.rag.retrieval import retrieve_documents
from config import RETRIEVAL_K

NO_ANSWER = (
    "К сожалению, я не нашёл подходящей информации "
    "в базе знаний STEREO AI."
)


def build_sources(documents):
    sources = []
    seen = set()

    for doc in documents:
        metadata = doc.metadata
        source = {
            "document_id": metadata.get("document_id", "Unknown"),
            "department": metadata.get("department", "Unknown"),
            "document_title": metadata.get("document_title", "Unknown"),
            "source_file": metadata.get("source_file", "Unknown"),
            "chunk_index": metadata.get("chunk_index"),
        }

        key = (source["document_id"], source["source_file"])
        if key not in seen:
            sources.append(source)
            seen.add(key)

    return sources


def ask_question(question: str, k: int = RETRIEVAL_K):
    """The single entry point for question answering."""
    documents = retrieve_documents(question, k=k)

    if not documents:
        return {"answer": NO_ANSWER, "sources": []}

    context = "\n\n".join(doc.page_content for doc in documents)
    answer = generate_answer(question, context)

    return {"answer": answer, "sources": build_sources(documents)}
