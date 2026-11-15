from pathlib import Path
import re

from app.rag.generation import generate_answer
from app.rag.ingestion import load_document
from app.rag.chunking import split_documents
from app.rag.retrieval import retrieve_documents
from app.rag.vector_store import save_documents

def index_directory(directory="data/documents"):
    documents = []

    files = sorted(Path(directory).rglob("*.docx"))

    if not files:
        raise ValueError("No DOCX documents found")

    print(f"Found {len(files)} DOCX files")

    for file_path in files:
        loaded_docs = load_document(str(file_path))

        full_text = "\n".join(doc.page_content for doc in loaded_docs)

        match = re.search(r"TN-\d{3}", full_text)
        document_id = match.group(0) if match else file_path.stem

        department = file_path.parent.name
        if "_" in department:
            department = department.split("_", 1)[1]
        department = department.replace("_", " ")

        metadata = {
            "document_id": document_id,
            "department": department,
            "document_title": file_path.stem.replace("_", " ").title(),
            "source_file": file_path.name,
            "file_format": "docx"
        }

        for doc in loaded_docs:
            doc.metadata.update(metadata)

        documents.extend(loaded_docs)

    chunks = split_documents(documents)

    counters = {}
    chunk_ids = []

    for chunk in chunks:
        doc_id = chunk.metadata["document_id"]
        chunk_number = counters.get(doc_id, 0)
        chunk.metadata["chunk_index"] = chunk_number

        chunk_ids.append(f"{doc_id}_{chunk_number:04d}")
        counters[doc_id] = chunk_number + 1

    BATCH_SIZE = 8
    indexed_count = 0

    for start in range(0, len(chunks), BATCH_SIZE):
        end = start + BATCH_SIZE

        batch_chunks = chunks[start:end]
        batch_ids = chunk_ids[start:end]

        save_documents(batch_chunks, ids=batch_ids)
        indexed_count += len(batch_chunks)

        print(f"Indexed {indexed_count}/{len(chunks)} chunks")

    return {
        "documents_loaded": len(files),
        "chunks_created": len(chunks),
        "chunks_indexed": indexed_count
    }

def answer_question(question: str) -> str:
    documents = retrieve_documents(question)

    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    answer = generate_answer(question, context)

    return answer