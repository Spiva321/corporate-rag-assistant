
import pytest

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings

from app.rag import retrieval


@pytest.fixture
def vector_store(tmp_path):
    embeddings = FakeEmbeddings(size=384)

    store = Chroma(
        collection_name="test_collection",
        embedding_function=embeddings,
        persist_directory=str(tmp_path / "chroma")
    )

    store.add_documents([
        Document(
            page_content="Employees receive 25 days of paid annual leave.",
            metadata={"department": "HR"}
        ),
        Document(
            page_content="The company reviews its budget every quarter.",
            metadata={"department": "Finance"}
        )
    ])

    yield store
    store.delete_collection()


def test_retrieval_returns_documents(vector_store):
    results = vector_store.similarity_search(
        "paid annual leave",
        k=2
    )

    assert len(results) > 0


def test_retrieval_content(vector_store):
    results = vector_store.similarity_search(
        "paid annual leave",
        k=2
    )

    contents = " ".join(
        doc.page_content for doc in results
    )

    assert "leave" in contents.lower()


def test_retrieval_metadata(vector_store):
    results = vector_store.similarity_search(
        "paid annual leave",
        k=2
    )

    assert any(
        doc.metadata.get("department") == "HR"
        for doc in results
    )


def test_retrieval_filters_weak_matches(monkeypatch):
    class FakeStore:
        def similarity_search_with_score(self, question, k):
            assert k == 6
            return [
                (Document(page_content="релевантно"), 0.2),
                (Document(page_content="нерелевантно"), 0.99),
            ]

    monkeypatch.setattr(retrieval, "get_vector_store", lambda: FakeStore())

    results = retrieval.retrieve_documents("вопрос", k=2)

    assert [doc.page_content for doc in results] == ["релевантно"]