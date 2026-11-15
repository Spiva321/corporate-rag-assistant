
from langchain_ollama import ChatOllama


def get_llm():
    return ChatOllama(
        model="qwen3:1.7b",
        temperature=0.1,
    )


def generate_answer(question: str, context: str) -> str:
    llm = get_llm()

    prompt = f"""
Ты — корпоративный AI-ассистент компании TechNova.

Отвечай на русском языке.
Используй только информацию из предоставленного контекста.
Не придумывай факты и цифры.
Если ответа нет в контексте, честно скажи, что информация не найдена.
Давай конкретные и понятные ответы.

КОНТЕКСТ:
{context}

ВОПРОС:
{question}

ОТВЕТ:
"""

    response = llm.invoke(prompt)

    return response.content
