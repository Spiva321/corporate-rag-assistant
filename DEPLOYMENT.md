# Развёртывание: Open WebUI + Tailscale

Сотрудники открывают только Open WebUI. Наш Flask и Ollama остаются на сервере и наружу не выходят.

```
Сотрудник → https://<сервер>.<tailnet>.ts.net
                 ↓  Tailscale Serve
           Open WebUI (Docker, 3000)
                 ↓  http://127.0.0.1:5000/v1
           Flask: /v1/models, /v1/chat/completions
                 ↓
           rag_service → Chroma + Ollama
```

## 1. Что должно быть на сервере

- Docker с Compose (`docker compose version`).
- Tailscale: `tailscale up`, сервер виден в `tailscale status`.
- Python 3.11+, `.venv` с зависимостями из `requirements.txt`.
- Ollama с моделями `bge-m3` и `qwen3:1.7b`.
- Проект: `git clone … && cd corporate-rag-assistant`.

Если сервер Linux, для доступа контейнера к хосту используется `host.docker.internal:host-gateway` — он уже прописан в `docker-compose.yml`.

## 2. Подготовка индекса и проверка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull bge-m3
ollama pull qwen3:1.7b

.venv/bin/python index_documents.py
.venv/bin/python -m pytest
```

Индекс `chroma_corporate_db/` не лежит в Git, поэтому шаг `index_documents.py` обязателен и после клонирования, и после изменения документов.

## 3. Запуск Flask (только локально)

Создайте `.env` в корне проекта при желании что-то переопределить:

```env
HOST=127.0.0.1
PORT=5000
OPENAI_MODEL_NAME=stereo-ai-rag
# OPENAI_API_KEY=свой_ключ   # если задан, Open WebUI должен прислать тот же ключ
```

Запуск:

```bash
.venv/bin/gunicorn --workers 1 --bind 127.0.0.1:5000 run:app
```

Проверка:

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/v1/models
```

Для постоянной работы оформите это как systemd-сервис:

```ini
[Unit]
Description=STEREO AI RAG API
After=network.target

[Service]
WorkingDirectory=/opt/corporate-rag-assistant
ExecStart=/opt/corporate-rag-assistant/.venv/bin/gunicorn -w 1 -b 127.0.0.1:5000 run:app
Restart=always
User=YOUR_USER

[Install]
WantedBy=multi-user.target
```

## 4. Запуск Open WebUI

```bash
docker compose up -d
docker compose logs -f open-webui
```

Стартовую страницу можно открыть с самого сервера: `http://127.0.0.1:3000` или по Tailscale-IP с портом: `http://100.x.y.z:3000`.

- При первом входе зарегистрируйте администратора.
- В `Settings → Connections → OpenAI API` адрес уже задан через переменные окружения:
  - Base URL: `http://host.docker.internal:5000/v1`
  - API Key: `dummy` (или тот, что задан в `OPENAI_API_KEY` на сервере)
- В списке моделей появится `stereo-ai-rag` — выберите её. Обычная `qwen3:1.7b` из Ollama тоже остаётся доступной.

Источники ответа (`CG-006` и т. д.) добавляются в конец текста ответа, поскольку в формате OpenAI они не передаются отдельно.

## 5. Доступ сотрудников через Tailscale

Самый аккуратный вариант — Tailscale Serve, который даёт HTTPS и имя без порта:

```bash
tailscale serve --bg 3000
tailscale serve status
```

Команда покажет адрес вида:

```
https://<сервер>.<tailnet>.ts.net
```

Его и рассылайте сотрудникам. Они должны быть в том же tailnet и иметь доступ по ACL. Альтернатива без Serve — `http://100.x.y.z:3000`, где `100.x.y.z` — Tailscale-IP сервера.

Публичный порт в фаерволе открывать не нужно: трафик идёт внутри туннеля Tailscale. При желании ограничьте доступ к порту 3000 через Tailscale ACL.

Отключить Serve: `tailscale serve --off`.

## 6. Что проверять после запуска

- `curl http://127.0.0.1:5000/health` → `healthy`, `chunks > 0`.
- `curl http://127.0.0.1:5000/v1/models` → модель `stereo-ai-rag`.
- В Open WebUI: вопрос «Что не завершено в проекте bonus_bot?» → ответ со ссылкой на `CG-006`.
- Вопрос «Какой SLA у P1 для клиента Premium?» → честный отказ: старой базы больше нет.

## 7. Обновления

- Изменились документы → `index_documents.py` (желательно с очисткой коллекции, см. README).
- Изменился код RAG → перезапустить gunicorn.
- Изменились переменные Open WebUI → `docker compose up -d`.

## Возможные проблемы

| Симптом | Что проверить |
|---|---|
| Модель `stereo-ai-rag` не появилась | `curl /v1/models` на сервере; `OPENAI_API_BASE_URL` и `extra_hosts` в compose |
| 500 вместо ответа | `/health`, логи gunicorn, доступность Ollama и наличие моделей |
| `chunks: 0` | выполнить `index_documents.py`; коллекция не коммитится в Git |
| Контейнер не видит хост | `host.docker.internal:host-gateway`, `docker compose logs open-webui` |
| Сотрудник не открывает сайт | `tailscale status`, `tailscale serve status`, ACL tailnet |
| 401 от нашего API | ключ в Open WebUI должен совпадать с `OPENAI_API_KEY` на сервере |
