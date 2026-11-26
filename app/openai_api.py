"""OpenAI-compatible API so Open WebUI can use our RAG as a model."""

import json
import time
import uuid

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    stream_with_context,
)

from app.rag.rag_service import ask_question
from config import OPENAI_API_KEY, OPENAI_MODEL_NAME, RETRIEVAL_K

openai_api = Blueprint("openai_api", __name__)


def api_error(message, status=400):
    return jsonify({
        "error": {
            "message": message,
            "type": "invalid_request_error",
            "param": None,
            "code": None,
        }
    }), status


def authorized():
    if not OPENAI_API_KEY:
        return True
    return request.headers.get("Authorization") == f"Bearer {OPENAI_API_KEY}"


def extract_question(messages):
    """Take the last user message; accept plain text or content parts."""
    if not isinstance(messages, list):
        return ""

    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue

        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            return " ".join(parts).strip()

    return ""


def format_answer(result):
    answer = result["answer"]
    document_ids = []

    for source in result.get("sources", []):
        document_id = source.get("document_id")
        if document_id and document_id not in document_ids:
            document_ids.append(document_id)

    if document_ids:
        answer += "\n\nИсточники: " + ", ".join(document_ids)

    return answer


def completion_id():
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


def completion_payload(answer):
    return {
        "id": completion_id(),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": OPENAI_MODEL_NAME,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "logprobs": None,
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def streamed_completion(answer):
    """Return the whole answer in one SSE chunk, then [DONE]."""
    response_id = completion_id()
    created = int(time.time())

    def chunks():
        first = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": OPENAI_MODEL_NAME,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant", "content": answer},
                "finish_reason": None,
            }],
        }
        last = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": OPENAI_MODEL_NAME,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }],
        }

        yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps(last, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(chunks()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@openai_api.route("/v1/models", methods=["GET"])
def models():
    if not authorized():
        return api_error("Invalid API key", 401)

    return jsonify({
        "object": "list",
        "data": [{
            "id": OPENAI_MODEL_NAME,
            "object": "model",
            "created": 0,
            "owned_by": "stereo-ai",
        }],
    })


@openai_api.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    if not authorized():
        return api_error("Invalid API key", 401)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Invalid JSON body")

    question = extract_question(data.get("messages"))
    if not question:
        return api_error("Question is required")

    try:
        result = ask_question(question, k=RETRIEVAL_K)
    except Exception:
        current_app.logger.exception("OpenAI-compatible chat request failed")
        return api_error(
            "Не удалось обработать вопрос. Проверь Ollama и ChromaDB.", 500
        )

    answer = format_answer(result)

    if data.get("stream"):
        return streamed_completion(answer)

    return jsonify(completion_payload(answer))
