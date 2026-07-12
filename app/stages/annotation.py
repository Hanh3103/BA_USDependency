import json
import time
from typing import Dict, Optional
from pathlib import Path

from pydantic import ValidationError

from connectionsHandle.ollama_connection import create_chat_completion
from errors.app_error import AppError
from errors.llm_errors import LLMConnectionError
from schemas.annotation_schema import AnnotationSchema


_prompt_path = Path(__file__).parent.parent / "prompts" / "annotation-prompts" / "annotation_v11.txt"
SYSTEM_PROMPT = _prompt_path.read_text()


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


def run(user_story: str, *, temperature_override: Optional[float] = None) -> Dict:
    response = create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_story},
        ],
        format=AnnotationSchema.model_json_schema()
    )

    if not response.message:
        raise AppError("Model returned no message")

    raw = response.message.content
    print(raw)

    if not raw:
        raise AppError("Model returned empty content")

    data = _extract_json(raw)
    try:
        validated = AnnotationSchema.model_validate(data)
    except ValidationError as exc:
        raise AppError(f"Annotation output did not match schema: {exc}") from exc

    result = {"Text": user_story, **validated.model_dump()}
    return result


def annotate(user_story: str, story_id: str, max_retries: int = 2) -> Optional[Dict]:
    last_error = None
    for attempt in range(max_retries):
        start = time.monotonic()
        try:
            annotation = run(user_story)
            elapsed = time.monotonic() - start
            print(f"  ✓ {story_id} annotated in {elapsed:.1f}s (attempt {attempt + 1})")
            annotation["id"] = story_id
            return annotation

        except LLMConnectionError as e:
            # Timeout or connection failure > don't crash the whole batch on this story.
            elapsed = time.monotonic() - start
            last_error = e
            print(f"  ⚠ {story_id} attempt {attempt + 1} timed out/failed after {elapsed:.1f}s: {e}")

        except AppError as e:
            elapsed = time.monotonic() - start
            last_error = e
            print(f"  ⚠ {story_id} attempt {attempt + 1} failed after {elapsed:.1f}s: {e}")

        except Exception as e:
            # Catch-all so one unexpected exception (e.g. malformed response object)
            # can't take down the entire batch run.
            elapsed = time.monotonic() - start
            last_error = e
            print(f"  ⚠ {story_id} attempt {attempt + 1} unexpected error after {elapsed:.1f}s: {e!r}")

    print(f"  ✗ Skipping {story_id} after {max_retries} attempts — last error: {last_error}")
    return None


def _save_results(results, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    from utils.file_parser import load_stories

    input_path = "test/test_raw_input/test_1.txt"
    output_path = "test/results/annotated_stories.json"
    print(f"Using prompt: {_prompt_path}")

    stories = load_stories(input_path)

    for story in stories:
        print(story + "\n")

    print("Warming up model...")
    warm_start = time.monotonic()
    try:
        create_chat_completion(
            messages=[{"role": "user", "content": "hi"}],
        )
        print(f"  ✓ Model warm after {time.monotonic() - warm_start:.1f}s")
    except LLMConnectionError as e:
        print(f"  ⚠ Warm-up failed: {e} — proceeding anyway, first story may be slow")

    results = []
    failed_ids = []

    for i, story in enumerate(stories):
        story_id = f"US-{i+1:03d}"
        print(f"  Annotating {story_id}...")

        ann = annotate(story, story_id)

        if ann:
            results.append(ann)
        else:
            failed_ids.append(story_id)

        # Save after every story, not just at the end — a crash or manual
        # interrupt (Ctrl+C) later in the run no longer loses everything
        # annotated so far.
        _save_results(results, output_path)

    print(f"\nDone.")
    print(f"  Annotated  : {len(results)} stories")
    print(f"  Failed     : {len(failed_ids)} stories {failed_ids if failed_ids else ''}")
    print(f"  Saved to   : {output_path}")
