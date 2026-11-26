from pathlib import Path
import re

from app.rag.chunking import split_documents
from app.rag.ingestion import load_document
from app.rag.rag_service import ask_question
from app.rag.vector_store import save_documents
from config import (
    DOCUMENT_ID_PATTERN,
    DOCUMENT_ID_SCAN_LINES,
    DOCUMENTS_DIRECTORY,
    INDEX_BATCH_SIZE,
    INDEX_EXTENSIONS,
)


def index_directory(directory=None):
    root = Path(directory) if directory is not None else DOCUMENTS_DIRECTORY
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in INDEX_EXTENSIONS
    )

    if not files:
        raise ValueError(f"No supported documents found in {root}")

    print(f"Found {len(files)} documents")

    documents = []
    seen_ids = {}
    next_generated_id = 1

    for file_path in files:
        loaded_docs = load_document(str(file_path))
        full_text = "\n".join(
            doc.page_content for doc in loaded_docs
        ).strip()

        if not full_text:
            raise ValueError(f"{file_path}: document contains no text")

        # Only the beginning of a document is authoritative: deeper in the
        # text the same shape matches hashes such as SHA-256.
        header = "\n".join(full_text.splitlines()[:DOCUMENT_ID_SCAN_LINES])
        match = re.search(DOCUMENT_ID_PATTERN, header)
        if match:
            document_id = match.group(0)
        else:
            # Markdown files have no code inside: assign a stable CG-xxx id.
            while True:
                document_id = f"CG-{next_generated_id:03d}"
                next_generated_id += 1
                if document_id not in seen_ids:
                    break

        if document_id in seen_ids:
            raise ValueError(
                f"Duplicate document id {document_id}: "
                f"{seen_ids[document_id]} and {file_path}"
            )
        seen_ids[document_id] = file_path

        department = file_path.parent.name
        if "_" in department:
            department = department.split("_", 1)[1]
        department = department.replace("_", " ")
        if department.islower():
            department = department.capitalize()

        metadata = {
            "document_id": document_id,
            "department": department,
            "document_title": file_path.stem.replace("_", " ").title(),
            "source_file": file_path.name,
            "file_format": file_path.suffix.lower().lstrip("."),
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

    indexed_count = 0

    for start in range(0, len(chunks), INDEX_BATCH_SIZE):
        end = start + INDEX_BATCH_SIZE
        batch = chunks[start:end]
        save_documents(batch, ids=chunk_ids[start:end])
        indexed_count += len(batch)
        print(f"Indexed {indexed_count}/{len(chunks)} chunks")

    return {
        "documents_loaded": len(files),
        "chunks_created": len(chunks),
        "chunks_indexed": indexed_count,
    }


def answer_question(question: str) -> str:
    """Backward-compatible helper: use the single RAG service."""
    return ask_question(question)["answer"]
