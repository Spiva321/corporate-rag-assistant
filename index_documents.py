from app.rag.pipeline import index_directory


if __name__ == "__main__":
    print("Starting TechNova knowledge base indexing...")

    result = index_directory("data/documents")

    print("\nIndexing completed!")
    print(result)