
from flask import Blueprint, jsonify, request, render_template

from app.rag.retrieval import retrieve_documents
from app.rag.generation import generate_answer

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@main.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "TechNova Knowledge Assistant"
    })


@main.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "Question is required"
        }), 400

    try:
        # 1. Search relevant documents in ChromaDB
        documents = retrieve_documents(question, k=3)

        if not documents:
            return jsonify({
                "question": question,
                "answer": "К сожалению, я не нашёл подходящей информации в базе знаний TechNova.",
                "sources": []
            })

        # 2. Prepare context
        context = "\n\n".join(
            doc.page_content for doc in documents
        )

        # 3. Generate answer using Qwen
        answer = generate_answer(question, context)

        # 4. Collect source information
        sources = []

        seen = set()

        for doc in documents:
            metadata = doc.metadata

            source = {
                "document_id": metadata.get("document_id", "Unknown"),
                "department": metadata.get("department", "Unknown"),
                "document_title": metadata.get("document_title", "Unknown"),
                "source_file": metadata.get("source_file", "Unknown")
            }

            key = (
                source["document_id"],
                source["source_file"]
            )

            if key not in seen:
                sources.append(source)
                seen.add(key)

        return jsonify({
            "question": question,
            "answer": answer,
            "sources": sources
        })

    except Exception:
        main.logger.exception("RAG chat request failed")

        return jsonify({
            "error": "Не удалось обработать вопрос. Проверь Ollama и ChromaDB."
        }), 500
