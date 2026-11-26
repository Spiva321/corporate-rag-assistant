from urllib.error import URLError
from urllib.request import urlopen

from flask import Blueprint, current_app, jsonify, request, render_template

from app.rag.rag_service import ask_question
from app.rag.vector_store import get_vector_store
from config import OLLAMA_BASE_URL, REQUEST_TIMEOUT, RETRIEVAL_K

main = Blueprint("main", __name__)


def ollama_available():
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        with urlopen(url, timeout=REQUEST_TIMEOUT) as response:
            return response.status == 200
    except (URLError, OSError, ValueError):
        return False


def indexed_chunks():
    try:
        # Chroma exposes no public count method on the LangChain wrapper.
        return get_vector_store()._collection.count()
    except Exception:
        current_app.logger.exception("Cannot read Chroma collection")
        return 0


@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@main.route("/health", methods=["GET"])
def health():
    ollama = ollama_available()
    chunks = indexed_chunks()
    healthy = ollama and chunks > 0

    return jsonify({
        "status": "healthy" if healthy else "degraded",
        "application": "STEREO AI Knowledge Assistant",
        "ollama": ollama,
        "chunks": chunks,
    }), 200 if healthy else 503


@main.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        result = ask_question(question, k=RETRIEVAL_K)
    except Exception:
        current_app.logger.exception("RAG chat request failed")
        return jsonify({
            "error": "Не удалось обработать вопрос. Проверь Ollama и ChromaDB."
        }), 500

    return jsonify({"question": question, **result})
