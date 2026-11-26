import pytest

from app import create_app
import app.routes as routes


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.content_type


def test_health_when_dependencies_are_ready(client, monkeypatch):
    monkeypatch.setattr(routes, "ollama_available", lambda: True)
    monkeypatch.setattr(routes, "indexed_chunks", lambda: 536)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "application": "STEREO AI Knowledge Assistant",
        "ollama": True,
        "chunks": 536,
    }


def test_health_is_degraded_without_index(client, monkeypatch):
    monkeypatch.setattr(routes, "ollama_available", lambda: True)
    monkeypatch.setattr(routes, "indexed_chunks", lambda: 0)

    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "degraded"


def test_chat_returns_answer_and_sources(client, monkeypatch):
    def fake_ask(question, k):
        return {
            "answer": "Ответ по базе знаний",
            "sources": [{"document_id": "TN-001"}],
        }

    monkeypatch.setattr(routes, "ask_question", fake_ask)

    response = client.post("/api/chat", json={"question": "Вопрос?"})
    assert response.status_code == 200
    assert response.get_json() == {
        "question": "Вопрос?",
        "answer": "Ответ по базе знаний",
        "sources": [{"document_id": "TN-001"}],
    }


def test_chat_rejects_empty_question(client):
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 400
    assert response.get_json() == {"error": "Question is required"}


def test_chat_returns_json_on_error(client, monkeypatch):
    def broken_ask(question, k):
        raise RuntimeError("boom")

    monkeypatch.setattr(routes, "ask_question", broken_ask)

    response = client.post("/api/chat", json={"question": "Вопрос?"})
    assert response.status_code == 500
    assert "error" in response.get_json()
