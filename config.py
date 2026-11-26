"""Centralized settings for the STEREO AI RAG demo.

Values can be overridden with environment variables or a local .env file.
"""

from pathlib import Path

from dotenv import load_dotenv

import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "qwen3:1.7b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
REQUEST_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "5"))

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "stereo_ai_corporate_kb")
PERSIST_DIRECTORY = Path(
    os.getenv("CHROMA_PERSIST_DIR") or (BASE_DIR / "chroma_corporate_db")
)
DOCUMENTS_DIRECTORY = Path(
    os.getenv("DOCUMENTS_DIR")
    or (BASE_DIR / "corporate_gpt_demo_knowledge")
)
INDEX_EXTENSIONS = (".md", ".docx", ".txt", ".pdf")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
INDEX_BATCH_SIZE = int(os.getenv("INDEX_BATCH_SIZE", "8"))

RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "3"))
RETRIEVAL_MAX_DISTANCE = float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.95"))
RETRIEVAL_CANDIDATE_MULTIPLIER = int(
    os.getenv("RETRIEVAL_CANDIDATE_MULTIPLIER", "3")
)

DOCUMENT_ID_PATTERN = r"\b[A-Z]{2,}-\d{3}\b"
DOCUMENT_ID_SCAN_LINES = 10

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "stereo-ai-rag")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
