from langchain_ollama import ChatOllama

class LLMService:
    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:1.7b",
            temperature=0.2
        )
    
    def generate_answer(self, question: str) -> str:
        response = self.llm.invoke(question)

        return response.content