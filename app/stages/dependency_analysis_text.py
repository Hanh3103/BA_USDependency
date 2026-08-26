from utils.llm_client_helpers import _call_stage, _load_prompt
from schemas.dependency.dependency_schema import TextDependencyResult
from config import settings
import json

TEXT_PROMPT_PATH = settings.prompt_path("dependency_analysis", variant="text")

def detect_dependency_text(story_a, story_b) -> TextDependencyResult:
    prompt = _load_prompt(TEXT_PROMPT_PATH)
    payload = {
        "story_a": {"id": story_a.id, "text": story_a.Text, "benefit": story_a.benefit},
        "story_b": {"id": story_b.id, "text": story_b.Text, "benefit": story_b.benefit},
    }

    messages = [
        {"role": "system", "content": prompt},

        # Example 1 - single direction
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "A",
                "text": "As a traveler, I want to add a new spot, so that I don't forget where I went.",
                "benefit": "so that I don't forget where I went",
            },
            "story_b": {
                "id": "B",
                "text": "As a planner, I want to attach a saved spot to my itinerary, so that my schedule is organized.",
                "benefit": "so that my schedule is organized",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "A", "story_b_id": "B", "dependencyFound": True,
            "dependencies": [{
                "prerequisite_id": "A", "dependent_id": "B",
                "explanationOfDependency": "In the main part of Story A, a 'spot' is created. This acts as a prerequisite for the main part of Story B, which attaches that saved 'spot'.",
                "matchingTextPairs": [["add a new spot", "attach a saved spot"]],
            }],
        })},

        # Example 2 - no dependency
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "A",
                "text": "As a user, I want to view my profile, so that I can see my details.",
                "benefit": "so that I can see my details",
            },
            "story_b": {
                "id": "B",
                "text": "As an admin, I want to browse system settings, so that I can configure the platform.",
                "benefit": "so that I can configure the platform",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "A", "story_b_id": "B", "dependencyFound": False, "dependencies": [],
        })},

        # Example 3 - bidirectional dependency
        {"role": "user", "content": json.dumps({
            "story_a": {
                "id": "A",
                "text": "As a planner, I want to create a trip and view an existing saved spot, so that I can add it to my plans.",
                "benefit": "so that I can add it to my plans",
            },
            "story_b": {
                "id": "B",
                "text": "As a traveler, I want to save a new spot and view an existing trip, so that I know where to attach it.",
                "benefit": "so that I know where to attach it",
            },
        })},
        {"role": "assistant", "content": json.dumps({
            "story_a_id": "A", "story_b_id": "B", "dependencyFound": True,
            "dependencies": [
                {
                    "prerequisite_id": "A", "dependent_id": "B",
                    "explanationOfDependency": "Story A creates a 'trip', which Story B views as an existing trip.",
                    "matchingTextPairs": [["create a trip", "view an existing trip"]],
                },
                {
                    "prerequisite_id": "B", "dependent_id": "A",
                    "explanationOfDependency": "Story B saves a new 'spot', which Story A views as an existing saved spot.",
                    "matchingTextPairs": [["save a new spot", "view an existing saved spot"]],
                },
            ],
        })},

        {"role": "user", "content": json.dumps(payload, indent=2)},
    ]

    try:
        return _call_stage(messages=messages, schema_model=TextDependencyResult)
    except Exception as err:
        print(f"Warning: Processing failed for pair ({story_a.id}, {story_b.id}): {err}")
        return TextDependencyResult(
            story_a_id=story_a.id, story_b_id=story_b.id,
            dependencyFound=False, dependencies=[],
        )
