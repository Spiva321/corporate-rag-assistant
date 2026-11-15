from langchain_chroma import Chroma

from app.rag.embeddings import get_embeddings

def get_vector_store():

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name="technova_corporate_kb",
        embedding_function=embeddings,
        persist_directory="./chroma_corporate_db"
    )

    return vector_store

def save_documents(chunks, ids=None):
    vector_store = get_vector_store()

    vector_store.add_documents(chunks, ids=ids)

    return len(chunks)