import pytest

from app.rag.ingestion import load_document


def test_load_docx(tmp_path):
    from docx import Document

    file_path = tmp_path / "test.docx"

    doc = Document()
    doc.add_paragraph("STEREO AI is a technology company.")
    doc.save(file_path)

    documents = load_document(str(file_path))

    assert len(documents) > 0
    assert "STEREO AI" in documents[0].page_content


def test_load_markdown(tmp_path):
    file_path = tmp_path / "note.md"
    file_path.write_text("# Заголовок\n\nТекст заметки.", encoding="utf-8")

    documents = load_document(str(file_path))

    assert len(documents) > 0
    assert "Заголовок" in documents[0].page_content
    assert "Текст заметки" in documents[0].page_content


def test_unsupported_format(tmp_path):
    file_path = tmp_path / "test.xlsx"
    file_path.write_text("test")

    with pytest.raises(ValueError):
        load_document(str(file_path))


def test_file_metadata(tmp_path):
    from docx import Document

    file_path = tmp_path / "metadata.docx"

    doc = Document()
    doc.add_paragraph("Employee onboarding process.")
    doc.save(file_path)

    documents = load_document(str(file_path))

    assert "source" in documents[0].metadata
