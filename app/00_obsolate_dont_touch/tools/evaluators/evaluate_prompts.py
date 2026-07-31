import csv
import json
import re
import sys
import time
from typing import Dict, List
from pathlib import Path

# Ensure `app` package is importable when running from the repository root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from errors import (
    PromptEvaluationError,
    PromptJSONParseError,
    PromptLoadError,
    PromptSchemaValidationError,
)
from schemas.annotation_schema import AnnotationSchema
from stages import ollama_connection


PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "annotation"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RESULTS_CSV = RESULTS_DIR / "results.csv"
RESULT_FIELDS = ["prompt", "user_story", "raw", "json_valid", "parsed", "error_type", "error"]


SAMPLES: List[str] = [
    "As a shopper, I want to save items to a wishlist so that I can purchase them later.",
    "As an admin, I want to export monthly sales reports to CSV so that I can analyze revenue.",
    "As a user, I want to receive push notifications for mentions so that I stay engaged.",
    "As a customer, I want to pay with multiple payment methods so that checkout is convenient.",
    "As a user, I want to enable two-factor authentication so that my account is more secure.",
]


def list_prompt_files() -> List[Path]:
    return sorted(
        [p for p in PROMPTS_DIR.rglob("*") if p.is_file() and p.suffix in (".txt", ".md")]
    )


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
                raise PromptJSONParseError("Model returned malformed JSON") from exc
        raise PromptJSONParseError("Model did not return JSON")


def fix_annotation_schema(data: dict) -> dict:
    """Normalize common annotation payload issues into the expected schema shape."""

    schema_fields = {
        "Text": "",
        "Persona": "",
        "GoalAction": [],
        "GoalEntity": [],
        "BenefitAction": [],
        "BenefitEntity": [],
        "triggers": [],
        "targets": [],
        "contains": [],
    }

    def as_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def as_nested_list(value):
        if value is None:
            return []
        if not isinstance(value, list):
            return [[value]]
        if not value:
            return []
        if all(not isinstance(item, list) for item in value):
            return [[str(item) for item in value]]
        return [[str(sub_item) for sub_item in item] if isinstance(item, list) else [str(item)] for item in value]

    normalized = {}
    source = data or {}

    for field_name, default_value in schema_fields.items():
        value = source.get(field_name, default_value)
        if field_name in {"Text", "Persona"}:
            normalized[field_name] = "" if value is None else str(value)
        elif field_name in {"GoalAction", "GoalEntity", "BenefitAction", "BenefitEntity"}:
            normalized[field_name] = [str(item) for item in as_list(value)]
        else:
            normalized[field_name] = as_nested_list(value)

    return normalized


def validate_annotation_output(data: dict) -> dict:
    """Validate annotation JSON against the annotation schema after repairing it."""

    try:
        validated = AnnotationSchema.parse_obj(fix_annotation_schema(data))
    except Exception as exc:
        raise PromptSchemaValidationError(f"Annotation output did not match schema: {exc}") from exc
    return validated.dict()


def _failure_result(prompt_path: Path, raw: str, exc: Exception) -> dict:
    return {
        "prompt": prompt_path.name,
        "raw": raw,
        "json_valid": False,
        "parsed": None,
        "error_type": type(exc).__name__,
        "error": str(exc),
    }


def _success_result(prompt_path: Path, raw: str, parsed: dict) -> dict:
    return {
        "prompt": prompt_path.name,
        "raw": raw,
        "json_valid": True,
        "parsed": parsed,
        "error_type": "",
        "error": "",
    }


def _load_prompt(prompt_path: Path) -> str:
    try:
        return prompt_path.read_text()
    except OSError as exc:
        raise PromptLoadError(f"Could not read prompt file {prompt_path.name}: {exc}") from exc


def run_one(prompt_path: Path, user_story: str) -> dict:
    raw = ""
    try:
        system_prompt = _load_prompt(prompt_path)
        resp = ollama_connection.create_chat_completion(
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_story}],
            temperature=0.0,
        )
        raw = resp.choices[0].message.content
        data = _extract_json(raw)
        validated = validate_annotation_output(data)

        return _success_result(prompt_path, raw, validated)
    except PromptEvaluationError as exc:
        return _failure_result(prompt_path, raw, exc)
    except Exception as exc:
        return _failure_result(prompt_path, raw, PromptEvaluationError(str(exc)))


def _write_results(rows: List[dict]) -> None:
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_all():
    prompts = list_prompt_files()
    if not prompts:
        print("No prompts found in", PROMPTS_DIR)
        return

    rows = []
    for prompt_path in prompts:
        print("Running prompt:", prompt_path.name)
        for sample in SAMPLES:
            print(" - sample:", sample[:60].replace('\n', ' '))
            row = run_one(prompt_path, sample)
            row["parsed"] = json.dumps(row["parsed"], ensure_ascii=False) if row["parsed"] is not None else ""
            rows.append(row)
            time.sleep(0.2)

    _write_results(rows)

    print("Results written to", RESULTS_CSV)


if __name__ == "__main__":
    run_all()
