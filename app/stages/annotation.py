import json
import re
from typing import Dict
from pathlib import Path

from pydantic import ValidationError

from connectionsHandle.ollama_connection import create_chat_completion
from errors.app_error import AppError
from schemas.annotation_schema import AnnotationSchema


_prompt_path = Path(__file__).parent.parent / "prompts" / "annotation-prompts" / "annotation_v2.txt"
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
        ]
    )

    raw = response.choices[0].message.content
    print(raw)
    data = _extract_json(raw)
    try:
        validated = AnnotationSchema.model_validate(data)
    except ValidationError as exc:
        raise AppError(f"Annotation output did not match schema: {exc}") from exc

    return validated.model_dump()

def annotate(user_story: str, story_id: str, max_retries: int = 2) -> Dict | None:
    for attempt in range(max_retries):
        try:
            annotation = run(user_story)
            annotation["id"] = story_id
            return annotation
        except AppError as e:
            print(f"  ⚠ Attempt {attempt + 1} failed for {story_id}: {e}")
    print(f"  ✗ Skipping {story_id} after {max_retries} attempts")
    return None


if __name__ == "__main__":
    from utils.file_parser import load_stories
    stories = load_stories("test_files/user_stories.txt")

    for story in stories:
        print(story + "\n")

    results = []

    for i, story in enumerate(stories):
        story_id = f"US-{i+1:03d}"
        print(f"  Annotating {story_id}...")
        ann = annotate(story, story_id)
        print(ann)
        if ann:
            results.append(ann)
    
    output_path = "tools/results/annotated_stories.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone.")
    print(f"  Annotated  : {len(results)} stories")
    print(f"  Saved to   : {output_path}")



