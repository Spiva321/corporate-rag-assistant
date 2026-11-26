from functools import lru_cache

from langchain_chroma import Chroma

from app.rag.embeddings import get_embeddings
from config import COLLECTION_NAME, PERSIST_DIRECTORY


@lru_cache(maxsize=1)
def get_vector_store():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(PERSIST_DIRECTORY),
    )


def save_documents(chunks, ids=None):
    vector_store = get_vector_store()
    vector_store.add_documents(chunks, ids=ids)
    return len(chunks)
