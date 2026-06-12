import json
import re
from typing import Dict
from pathlib import Path

from pydantic import ValidationError

from stages.ollama_connection import create_chat_completion
from errors.app_error import AppError
from schemas.annotation_schema import AnnotationSchema


_prompt_path = Path(__file__).parent.parent / "prompts" / "annotation-prompts" / "annotation.txt"
SYSTEM_PROMPT = _prompt_path.read_text()


def _extract_json(text: str) -> Dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError as exc:
                raise AppError("Model returned malformed JSON") from exc
        raise AppError("Model did not return JSON")


def run(user_story: str) -> Dict:
    response = create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_story},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content
    data = _extract_json(raw)
    try:
        validated = AnnotationSchema.parse_obj(data)
    except ValidationError as exc:
        raise AppError(f"Annotation output did not match schema: {exc}") from exc

    return validated.dict()
