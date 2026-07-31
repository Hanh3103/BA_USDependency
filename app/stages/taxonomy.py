import json

from schemas.dependency.dependency_schema import Taxonomy, StoryActivity
from utils.llm_client_helpers import _load_prompt, _call_stage
from config import settings

PROMPT_TAXONOMY_PATH= settings.prompt_path("dependency_analysis", step=1)


def collect_distinct_verbs(stories: list[StoryActivity]) -> list[str]:
    """Extracts and deduplicates all GoalAction verbs across well-formed stories."""
    verbs = {activity.action for story in stories for activity in story.activity}
    return sorted(list(verbs))


def build_verb_taxonomy(distinct_verbs: list[str]) -> Taxonomy:
    """Builds the global verb taxonomy in a single LLM execution."""
    taxonomy_prompt = _load_prompt(PROMPT_TAXONOMY_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": taxonomy_prompt},
            {"role": "user", "content": f"Verb list:\n{json.dumps(distinct_verbs, indent=2)}"},
        ],
        schema_model=Taxonomy,
    )
