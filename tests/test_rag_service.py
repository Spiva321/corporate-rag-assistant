from langchain_core.documents import Document

from app.rag import rag_service


def test_build_sources_deduplicates_chunks_of_same_file():
    metadata = {
        "document_id": "TN-001",
        "department": "HR",
        "document_title": "Tn 001 Company Overview",
        "source_file": "TN-001_Company_Overview.docx",
    }
    documents = [
        Document(page_content="a", metadata={**metadata, "chunk_index": 0}),
        Document(page_content="b", metadata={**metadata, "chunk_index": 1}),
    ]

    sources = rag_service.build_sources(documents)

    assert len(sources) == 1
    assert sources[0]["chunk_index"] == 0


def test_ask_question_without_relevant_documents(monkeypatch):
    monkeypatch.setattr(rag_service, "retrieve_documents", lambda q, k: [])

    result = rag_service.ask_question("Вопрос")

    assert result["sources"] == []
    assert "не нашёл" in result["answer"]
