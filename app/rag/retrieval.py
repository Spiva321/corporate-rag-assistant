from app.rag.vector_store import get_vector_store

def retrieve_documents(question: str, k: int = 3):
    vector_store = get_vector_store()

    result = vector_store.similarity_search(question, k=k)

    return result