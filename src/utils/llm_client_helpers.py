import json
from pathlib import Path
from typing import Dict, List, TypeVar, Type

from pydantic import ValidationError, BaseModel

from src.connectionsHandle.ollama_connection import create_chat_completion
from src.errors import AppError

T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> Dict:
    """Extract the first balanced {...} object instead of greedily matching
    from the first '{' to the LAST '}' in the response (which can swallow
    trailing commentary or multiple JSON-like fragments)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise AppError("Model did not return JSON")

    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as exc:
                    raise AppError("Model returned malformed JSON") from exc

    raise AppError("Model returned unterminated JSON")


def _call_stage(messages: List[Dict], schema_model: Type[T], model: str) -> T:
    """
    Single constrained call against a running convesation, validated against schema_model.
    """
    response = create_chat_completion(
        messages= messages,
        model=model,
        format=schema_model.model_json_schema()
    )

    if not response.message:
        raise AppError("Model returned no messsage")

    raw = response.message.content

    if not raw:
        raise AppError("Model returned empty content")

    data = _extract_json(raw)

    try:
        return schema_model.model_validate(data)
    except ValidationError as exc:
        raise AppError (f"Model output did not match schema: {exc}") from exc


def _load_prompt(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError as exc:
        raise AppError(f"Prompt file not found: {path}") from exc
