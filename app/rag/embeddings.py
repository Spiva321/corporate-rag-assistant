from langchain_ollama import OllamaEmbeddings

def get_embeddings():

    embeddings = OllamaEmbeddings(
        model='bge-m3',
        base_url='http://localhost:11434'
    )

    return embeddings