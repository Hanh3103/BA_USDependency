from functools import lru_cache

from openai import APIConnectionError, APITimeoutError, OpenAI

from errors.llm_errors import LLMConnectionError

BASE_URL = "http://ollama:11434/v1"
API_KEY = "ollama"
MODEL = ["qwen2.5:0.5b", "llama3:0.5b", "gemini-1.5-pro:0.5b"]


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    return OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
    )


def create_chat_completion(*, messages, temperature: float = 0.1, model: str = MODEL[0]):
    try:
        return get_openai_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
    except (APIConnectionError, APITimeoutError) as exc:
        raise LLMConnectionError("Failed to connect to the model service.") from exc