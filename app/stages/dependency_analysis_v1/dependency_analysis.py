from utils.llm_client_helpers import _call_stage, _load_prompt
from schemas.dependency.dependency_schema import StoryActivity, Taxonomy, VerbClassifyResult, EntityMatchResult, FoundedDependencyUsingAnnotated, PairResult
from config import settings

CLASSIFY_PROMPT_PATH =settings.prompt_path("dependency_analysis", step=2)
ENTITY_MATCH_PATH = settings.prompt_path("dependency_analysis", step=3)
DECISION_PROMPT_PATH = settings.prompt_path("dependency_analysis", step=4)



def classify_activities(story_a: StoryActivity, story_b: StoryActivity, taxonomy: Taxonomy) -> VerbClassifyResult:
    classify_prompt = _load_prompt(CLASSIFY_PROMPT_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": classify_prompt},
            {"role": "assistant", "content": f"Verb taxonomy context:\n{taxonomy.model_dump_json(indent=2)}"},
            {"role": "user", "content": f"Story a:\n{story_a.model_dump_json(indent=2)}\n\nStory b:\n{story_b.model_dump_json(indent=2)}"},
            {"role": "user", "content": "Classify the activities in these stories using the provided taxonomy."}
        ],
        schema_model=VerbClassifyResult
    )


def find_entity_matches(step2_output: VerbClassifyResult) -> EntityMatchResult:

    entity_prompt = _load_prompt(ENTITY_MATCH_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": entity_prompt},
            {"role": "assistant", "content": step2_output.model_dump_json(indent=2)},
            {"role": "user", "content": "Find candidate matches based on the classified activities above."}
        ],
        schema_model=EntityMatchResult
    )


def decide_dependency(step3_output: EntityMatchResult) -> FoundedDependencyUsingAnnotated:
    """Step 4: apply PROVISIONS -> REQUIRES direction rules and produce the final verdict."""
    decision_prompt = _load_prompt(DECISION_PROMPT_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": decision_prompt},
            {"role": "assistant", "content": step3_output.model_dump_json(indent=2)},
            {"role": "user", "content": "Produce the final dependency verdict based on these candidate matches."}
        ],
        schema_model=FoundedDependencyUsingAnnotated
    )


def detect_dependency(story_a: StoryActivity, story_b: StoryActivity, taxonomy: Taxonomy) -> PairResult:
    step_2 = classify_activities(story_a, story_b, taxonomy)
    step_3 = find_entity_matches(step_2)
    step_4 = decide_dependency(step_3)


    return PairResult(story_a=story_a.Text, story_b=story_b.Text, step_2_classify=step_2, step_3_match=step_3, final=step_4)



