from app.rag.pipeline import index_directory
from config import DOCUMENTS_DIRECTORY

if __name__ == "__main__":
    print("Starting STEREO AI knowledge base indexing...")

    result = index_directory(DOCUMENTS_DIRECTORY)

    print("\nIndexing completed!")
    print(result)
