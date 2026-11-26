import pytest
from langchain_core.documents import Document

import app.rag.pipeline as pipeline


def make_docx(tmp_path, folder, name):
    directory = tmp_path / folder
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(b"fake docx")
    return path


def test_index_directory_extracts_metadata(tmp_path, monkeypatch):
    make_docx(tmp_path, "02_Finance", "KB-042_Vendor_Policy.docx")

    monkeypatch.setattr(
        pipeline,
        "load_document",
        lambda path: [Document(page_content="KB-042 — политика закупок")],
    )

    captured = {}

    def fake_save(chunks, ids=None):
        captured["chunks"] = list(chunks)
        captured["ids"] = list(ids)
        return len(chunks)

    monkeypatch.setattr(pipeline, "save_documents", fake_save)

    result = pipeline.index_directory(tmp_path)

    assert result == {
        "documents_loaded": 1,
        "chunks_created": 1,
        "chunks_indexed": 1,
    }

    metadata = captured["chunks"][0].metadata
    assert metadata["document_id"] == "KB-042"
    assert metadata["department"] == "Finance"
    assert metadata["source_file"] == "KB-042_Vendor_Policy.docx"
    assert captured["ids"] == ["KB-042_0000"]


def test_index_directory_assigns_ids_to_markdown(tmp_path, monkeypatch):
    directory = tmp_path / "ecosystem"
    directory.mkdir()
    (directory / "research_notes.md").write_text(
        "# Исследование", encoding="utf-8"
    )

    monkeypatch.setattr(
        pipeline,
        "load_document",
        lambda path: [Document(page_content="Содержимое без кода")],
    )
    captured = {}
    monkeypatch.setattr(
        pipeline,
        "save_documents",
        lambda chunks, ids=None: captured.update(
            chunks=list(chunks), ids=list(ids)
        ),
    )

    result = pipeline.index_directory(tmp_path)

    assert result["documents_loaded"] == 1
    metadata = captured["chunks"][0].metadata
    assert metadata["document_id"] == "CG-001"
    assert metadata["department"] == "Ecosystem"
    assert metadata["file_format"] == "md"
    assert captured["ids"] == ["CG-001_0000"]


def test_index_directory_ignores_hashes_deep_in_text(tmp_path, monkeypatch):
    (tmp_path / "notes.md").write_text("# Заметка", encoding="utf-8")
    monkeypatch.setattr(
        pipeline,
        "load_document",
        lambda path: [
            Document(page_content="Строка\n" * 15 + "Хэш SHA-256")
        ],
    )
    captured = {}
    monkeypatch.setattr(
        pipeline,
        "save_documents",
        lambda chunks, ids=None: captured.update(
            chunks=list(chunks), ids=list(ids)
        ),
    )

    pipeline.index_directory(tmp_path)

    assert captured["chunks"][0].metadata["document_id"] == "CG-001"


def test_index_directory_rejects_duplicate_ids(tmp_path, monkeypatch):
    make_docx(tmp_path, "02_Finance", "KB-042_First.docx")
    make_docx(tmp_path, "03_IT", "KB-042_Second.docx")

    monkeypatch.setattr(
        pipeline,
        "load_document",
        lambda path: [Document(page_content="KB-042 — документ")],
    )

    with pytest.raises(ValueError, match="Duplicate document id"):
        pipeline.index_directory(tmp_path)


def test_index_directory_rejects_empty_documents(tmp_path, monkeypatch):
    make_docx(tmp_path, "02_Finance", "KB-042_Empty.docx")

    monkeypatch.setattr(
        pipeline,
        "load_document",
        lambda path: [Document(page_content="   ")],
    )

    with pytest.raises(ValueError, match="contains no text"):
        pipeline.index_directory(tmp_path)


def test_answer_question_uses_single_service(monkeypatch):
    monkeypatch.setattr(
        pipeline, "ask_question", lambda question: {"answer": "Ответ"}
    )

    assert pipeline.answer_question("Вопрос") == "Ответ"
