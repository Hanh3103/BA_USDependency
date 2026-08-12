from utils.llm_client_helpers import _call_stage, _load_prompt
from schemas.dependency.dependency_schema import StoryActivity, EntityMatchResult, ClassifiedMatchResult, DependencyResult, PairResult
from config import settings

ENTITY_PROMPT_PATH =settings.prompt_path("dependency_analysis", step=1)
CLASSIFY_PROMPT_PATH = settings.prompt_path("dependency_analysis", step=2)
DECISION_PROMPT_PATH = settings.prompt_path("dependency_analysis", step=3)



def find_entity_matches(story_a:StoryActivity, story_b:StoryActivity) -> EntityMatchResult:

    entity_prompt = _load_prompt(ENTITY_PROMPT_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": entity_prompt},
            {"role": "user", "content": f"Story a:\n{story_a.model_dump_json(indent=2)}\n\nStory b:\n{story_b.model_dump_json(indent=2)}"},
            {"role": "user", "content": "Find candidate entity matches between these two stories."}
        ],
        schema_model=EntityMatchResult
    )


def classify_activities(step1_output: EntityMatchResult) -> ClassifiedMatchResult:
    classify_prompt = _load_prompt(CLASSIFY_PROMPT_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": classify_prompt},
            {"role": "assistant", "content": step1_output.model_dump_json(indent=2)},
            {"role": "user", "content": "Classify the operation_type of each activity in these matches."}
        ],
        schema_model=ClassifiedMatchResult
    )

def decide_dependency(step2_output: ClassifiedMatchResult) -> DependencyResult:
    """Step 4: apply PROVISIONS -> REQUIRES direction rules and produce the final verdict."""
    decision_prompt = _load_prompt(DECISION_PROMPT_PATH)

    return _call_stage(
        messages=[
            {"role": "system", "content": decision_prompt},
            {"role": "assistant", "content": step2_output.model_dump_json(indent=2)},
            {"role": "user", "content": "Produce the final dependency verdict based on these candidate matches."}
        ],
        schema_model=DependencyResult
    )


def detect_dependency(story_a: StoryActivity, story_b: StoryActivity) -> PairResult:
    step_1 = find_entity_matches(story_a, story_b)
    step_2 = classify_activities(step_1)
    step_3 = decide_dependency(step_2)


    return PairResult(story_a=story_a.Text, story_b=story_b.Text, step_1_match=step_1, step_2_classify=step_2, final=step_3)



