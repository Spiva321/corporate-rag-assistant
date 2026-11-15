
from langchain_core.documents import Document

from app.rag.chunking import split_documents


def test_split_documents():
    text = "TechNova employee policy. " * 200

    documents = [
        Document(
            page_content=text,
            metadata={"department": "HR"}
        )
    ]

    chunks = split_documents(documents)

    assert len(chunks) > 1


def test_chunk_size():
    text = "TechNova employee policy. " * 200

    documents = [Document(page_content=text)]

    chunks = split_documents(documents)

    for chunk in chunks:
        assert len(chunk.page_content) <= 500


def test_metadata_preserved():
    documents = [
        Document(
            page_content="Employee vacation policy.",
            metadata={"department": "HR"}
        )
    ]

    chunks = split_documents(documents)

    assert chunks[0].metadata["department"] == "HR"
