from functools import lru_cache
from typing import Optional, Union, Literal

from httpx import RequestError
from ollama import Client, ResponseError, ChatResponse

from errors.llm_errors import LLMConnectionError
from config import settings

#BASE_URL = "http://ollama:11434/v1"  # this line for docker


@lru_cache(maxsize=1)
def get_ollama_client() -> Client:
    return Client(
        host=settings.ollama_base_url,
        headers={"Authorization": f"Bearer {settings.ollama_api_key}"} if settings.ollama_api_key else None,
        timeout=180.0,
    )


def create_chat_completion(
        *,
        messages: list[dict],
        model: str,
        format: Optional[Union[Literal['', 'json'], dict]] = None,
):
    try:
        response =  get_ollama_client().chat(
            model=model,
            messages=messages,
            stream= False,
            format= format if format is not None else settings.ollama_format,
            options={
                "temperature": settings.ollama_temperature,
                "top_p": settings.ollama_top_p,
                "num_predict": settings.ollama_num_predict,
                "num_ctx": settings.ollama_num_ctx,
            },
            keep_alive=settings.ollama_keep_alive,
            think=settings.ollama_think,
        )
        assert response.model == model, f"Requested {model!r}, Ollama served {response.model!r}"
        return response
    except (RequestError, ResponseError) as exc:
        raise LLMConnectionError(f"{exc.__class__.__name__}: {exc}") from exc