from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)


def load_document(file_path: str):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(str(path))
    elif extension == ".docx":
        loader = Docx2txtLoader(str(path))
    elif extension in (".txt", ".md"):
        loader = TextLoader(
            str(path), encoding="utf-8", autodetect_encoding=True
        )
    else:
        raise ValueError(f"Unsupported file format: {extension}")

    try:
        documents = loader.load()
    except Exception as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc

    if not documents or not any(
        doc.page_content.strip() for doc in documents
    ):
        raise ValueError(f"Document contains no text: {path}")

    return documents
