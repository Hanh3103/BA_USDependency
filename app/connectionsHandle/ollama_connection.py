from functools import lru_cache

from openai import APIConnectionError, APITimeoutError, OpenAI

from errors.llm_errors import LLMConnectionError
from config import settings

#BASE_URL = "http://ollama:11434/v1"  # this line for docker

print(settings.models[0])


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    return OpenAI(
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
        timeout=60.0,
    )


def create_chat_completion(*, messages, model: str = settings.models[0]):
    try:
        return get_openai_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=settings.ollama_temperature,
            top_p=settings.ollama_top_p,
            extra_body={
                "keep_alive": settings.ollama_keep_alive,
                "think": settings.ollama_think,
            }
        )
    except (APIConnectionError, APITimeoutError) as exc:
        raise LLMConnectionError("Failed to connect to the model service.") from exc