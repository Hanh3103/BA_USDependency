import json
import time
from typing import Dict, Optional, Literal
import argparse
from src.errors import AppError
from src.errors.llm_errors import LLMConnectionError
from schemas.annotation.annotation_schema import AnnotationSchema, Step1Schema, Step2Schema, Step3Schema
from config import settings
from utils.llm_client_helpers import _call_stage, _load_prompt

SINGLE_PROMPT_PATH = settings.prompt_path("annotation")
STAGE1_PROMPT_PATH = settings.prompt_path("annotation", step=1)
STAGE2_PROMPT_PATH = settings.prompt_path("annotation", step=2)
STAGE3_PROMPT_PATH = settings.prompt_path("annotation", step=3)


MODE = Literal["single", "sequential"]


def _run_single(user_story: str, model:str) -> AnnotationSchema:
    """
    Run a single-step annotation process.

    Args:
        user_story: The user story to annotate.
        model: The name of the model to use.

    Returns:
        The annotated user story.
    """
    prompt = _load_prompt(SINGLE_PROMPT_PATH)
    return _call_stage(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_story},
        ],
        schema_model= AnnotationSchema,
        model=model,
    )


def _run_3steps(user_story: str, model:str) -> AnnotationSchema:
    """
    Run a three-step annotation process.

    Args:
        user_story: The user story to annotate.
        model: The name of the model to use.

    Returns:
        The annotated user story.
    """
    # STEP 1: Extract raw components
    step1_prompt = _load_prompt(STAGE1_PROMPT_PATH)
    step1_res = _call_stage(
        messages=[
            {"role": "system", "content": step1_prompt},
            {"role": "user", "content": user_story},
        ],
        schema_model=Step1Schema,
        model=model,
    )

    # STEP 2: Classify into Goal/Benefit concepts
    step2_prompt = _load_prompt(STAGE2_PROMPT_PATH)
    step2_res = _call_stage(
        messages=[
            {"role": "system", "content": step2_prompt},
            {"role": "user", "content": user_story},
            {"role": "assistant", "content": step1_res.model_dump_json(indent=2)},
            {"role": "user", "content": "Classify the extracted Actions and Entities into Goal and Benefit concepts."},
        ],
        schema_model=Step2Schema,
        model=model,
    )

    # STEP 3: Extract relationships (triggers, targets, contains)
    step3_prompt = _load_prompt(STAGE3_PROMPT_PATH)

    # Combine nodes to feed into Step 3
    node_context = {
        "Persona": step1_res.Persona,
        "Action": step2_res.Action.model_dump(),
        "Entity": step2_res.Entity.model_dump(),
        "benefit": step1_res.benefit
    }

    step3_res = _call_stage(
        messages=[
            {"role": "system", "content": step3_prompt},
            {"role": "user", "content": user_story},
            {"role": "assistant", "content": json.dumps(node_context, indent=2)},
            {"role": "user",
             "content": "Using only the nodes listed above, extract the triggers, targets, and contains edges."},
        ],
        schema_model=Step3Schema,
        model=model
    )

    # Combine all steps into the final result
    return AnnotationSchema(
        Persona=step1_res.Persona,
        Action=step2_res.Action,
        Entity=step2_res.Entity,
        benefit=step1_res.benefit,
        triggers=step3_res.triggers,
        targets=step3_res.targets,
        contains=step3_res.contains,
    )

# main run

def run(user_story: str, *, mode: MODE = "sequential", temperature_override: Optional[float] = None, model: str) -> Dict:
    """
    Run the annotation process on a user story.

    Args:
        user_story: The user story to annotate.
        mode: The mode of annotation, either "single" or "sequential".
        temperature_override: Optional temperature setting for the model.
        model: The name of the model to use.

    Returns:
        A dictionary containing the annotated user story and the mode used.
    """
    if mode == "single":
        validated = _run_single(user_story, model=model)
    elif mode == "sequential":
        validated = _run_3steps(user_story, model=model)
    else:
        raise ValueError(f"Unknown mode: {mode!r} (expected 'single' or 'sequential')")

    result = {"Text": user_story, "mode": mode, **validated.model_dump()}
    return result


def annotate(user_story: str,story_id:str, model: str, max_retries: int = 2, mode: MODE = "sequential") -> Optional[Dict]:
    """
    Annotate a user story with retries in case of failures.

    Args:
        user_story: The user story to annotate.
        story_id: An identifier for the user story.
        model: The name of the model to use.
        max_retries: The maximum number of retries in case of failure.
        mode: The mode of annotation, either "single" or "sequential".

    Returns:
        A dictionary containing the annotated user story, runtime, and number of attempts, or None if all attempts fail.

    """
    last_error = None
    for attempt in range(max_retries):
        start = time.monotonic()
        try:
            annotation = run(user_story, mode=mode, model=model)
            elapsed = time.monotonic() - start
            print(f"{story_id} annotated in {elapsed:.1f}s (attempt {attempt + 1}, mode={mode})")
            return {
                "story_id": story_id,
                "annotation": annotation,
                "runtime_sec": round(elapsed, 3),
                "attempts": attempt + 1,
            }

        except LLMConnectionError as e:
            elapsed = time.monotonic() - start
            last_error = e
            print(f"{story_id} attempt {attempt + 1} timed out/failed after {elapsed:.1f}s: {e}")

        except AppError as e:
            elapsed = time.monotonic() - start
            last_error = e
            print(f"{story_id} attempt {attempt + 1} failed after {elapsed:.1f}s: {e}")

        except Exception as e:
            elapsed = time.monotonic() - start
            last_error = e
            print(f"{story_id} attempt {attempt + 1} unexpected error after {elapsed:.1f}s: {e!r}")

    print(f"Skipping {story_id} after {max_retries} attempts — last error: {last_error}")
    return None


if __name__ == "__main__":
    from utils.file_parser import load_raw_stories
    from utils.file_writer import save_results

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["sequential", "single"], default="sequential")
    parser.add_argument("--model", default="qwen3:1.7b")
    args = parser.parse_args()


    input_path = "test/test_raw_input/test_1.txt"
    output_path = f"test/results/annotated_stories_{args.mode}.json"
    print(f"Mode: {args.mode}")

    stories = load_raw_stories(input_path)

    for story in stories:
        print(story)


    results = []
    failed_text = []

    for i, story in enumerate(stories):
        story_id = f"US-{i+1:03d}"
        ann = annotate(story, story_id=story_id, mode=args.mode, model=args.model)
        if ann:
            results.append(ann)
        else:
            failed_text.append(story)

        save_results(results, output_path, indent=2)

    print(f"\nDone.")
    print(f"  Annotated  : {len(results)} stories")
    print(f"  Failed     : {len(failed_text)} stories {failed_text if failed_text else ''}")
    print(f"  Saved to   : {output_path}")
