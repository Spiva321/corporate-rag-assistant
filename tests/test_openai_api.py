import pytest

from app import create_app
import app.openai_api as openai_api


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def fake_ask(monkeypatch):
    def ask(question, k):
        assert question == "Что не завершено?"
        return {
            "answer": "Ответ по базе знаний",
            "sources": [
                {"document_id": "CG-006", "source_file": "wallet.md"},
                {"document_id": "CG-006", "source_file": "wallet.md"},
            ],
        }

    monkeypatch.setattr(openai_api, "ask_question", ask)
    return ask


def test_models(client):
    response = client.get("/v1/models")

    assert response.status_code == 200
    data = response.get_json()
    assert data["object"] == "list"
    assert data["data"][0]["id"] == "stereo-ai-rag"


def test_chat_completion(client, fake_ask):
    response = client.post("/v1/chat/completions", json={
        "model": "stereo-ai-rag",
        "messages": [
            {"role": "system", "content": "Ты ассистент"},
            {"role": "user", "content": "Что не завершено?"},
        ],
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "stereo-ai-rag"
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"] == (
        "Ответ по базе знаний\n\nИсточники: CG-006"
    )
    assert data["choices"][0]["finish_reason"] == "stop"


def test_chat_completion_with_stream(client, fake_ask):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "Что не завершено?"}],
        "stream": True,
    })

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    body = response.get_data(as_text=True)
    assert "Источники: CG-006" in body
    assert "[DONE]" in body
    assert '"finish_reason": "stop"' in body


def test_chat_completion_rejects_empty_question(client):
    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "   "}],
    })

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == "Question is required"


def test_chat_completion_returns_error_on_failure(client, monkeypatch):
    def broken(question, k):
        raise RuntimeError("boom")

    monkeypatch.setattr(openai_api, "ask_question", broken)

    response = client.post("/v1/chat/completions", json={
        "messages": [{"role": "user", "content": "Вопрос"}],
    })

    assert response.status_code == 500
    assert "error" in response.get_json()


def test_api_key_is_checked_when_configured(client, monkeypatch):
    monkeypatch.setattr(openai_api, "OPENAI_API_KEY", "secret")

    denied = client.get("/v1/models")
    allowed = client.get(
        "/v1/models", headers={"Authorization": "Bearer secret"}
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200
