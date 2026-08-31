from utils.llm_client_helpers import _call_stage, _load_prompt
from schemas.dependency.dependency_schema import (
    StoryActivity, ActionEntityPair,PairMatchVerdict, EntityMatchResult, ActivityPairInput, ClassifiedMatch, ClassifiedActivityPair,
    ClassifiedMatchResult, ClassifiedActivityPairInput, DependencyVerdict, FoundedDependencyUsingAnnotated,DependencyEntryAnnotated, AnnotatedDependencyResult)
from itertools import product
import json
from config import settings

ENTITY_PROMPT_PATH =settings.prompt_path("dependency_analysis", variant="annotated", step=1)
CLASSIFY_PROMPT_PATH = settings.prompt_path("dependency_analysis", variant="annotated", step=2)
DECISION_PROMPT_PATH = settings.prompt_path("dependency_analysis", variant="annotated", step=3)


def cartesian_activity_pairs(story_a: StoryActivity, story_b: StoryActivity) -> list[tuple[ActionEntityPair, ActionEntityPair]]:
    return list(product(story_a.activity, story_b.activity))

def find_entity_matches(story_a: StoryActivity, story_b: StoryActivity, model:str) -> EntityMatchResult:
    entity_prompt = _load_prompt(ENTITY_PROMPT_PATH)
    candidate_pairs = cartesian_activity_pairs(story_a, story_b)

    entity_matches = []
    for a, b in candidate_pairs:
        pair_json = json.dumps(
            {"activity_a": a.model_dump(), "activity_b": b.model_dump()}, indent=2
        )
        result = _call_stage(
            messages=[
                {"role": "system", "content": entity_prompt},
                {
                    "role": "user",
                    "content": (
                        "Candidate pair:\n"
                        "{\n"
                        '  "activity_a": {"action": "create", "entity": "invoice"},\n'
                        '  "activity_b": {"action": "update", "entity": "existing invoice"}\n'
                        "}"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{"match_type": "semantic", "explanation": '
                        '"\'existing invoice\' is the same invoice in an already-created state."}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Candidate pair:\n"
                        "{\n"
                        '  "activity_a": {"action": "log out", "entity": "account"},\n'
                        '  "activity_b": {"action": "view", "entity": "account"}\n'
                        "}"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{"match_type": "exact", "explanation": '
                        '"Both activities reference the identical entity string \'account\'."}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Candidate pair:\n"
                        "{\n"
                        '  "activity_a": {"action": "view", "entity": "order history"},\n'
                        '  "activity_b": {"action": "print", "entity": "receipt"}\n'
                        "}"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{"match_type": "other", "explanation": '
                        '"Order history and a receipt are related but distinct entities."}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Candidate pair:\n"
                        "{\n"
                        '  "activity_a": {"action": "view", "entity": "playlist"},\n'
                        '  "activity_b": {"action": "reset", "entity": "password"}\n'
                        "}"
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{"match_type": "other", "explanation": '
                        '"Playlist and password are unrelated entities."}'
                    ),
                },
                {"role": "user", "content": f"Candidate pair:\n{pair_json}"},
            ],
            schema_model=PairMatchVerdict,
            model=model
        )
        if result.match_type in ("exact", "semantic"):
            entity_matches.append({
                "activity_a": a,
                "activity_b": b,
                "match_type": result.match_type,
                "explanation": result.explanation,
            })

    return EntityMatchResult(
        story_a_id=story_a.id,
        story_b_id=story_b.id,
        entity_matches=entity_matches,
    )


def classify_activities(step1_output: EntityMatchResult, model:str) -> ClassifiedMatchResult:
    classify_prompt = _load_prompt(CLASSIFY_PROMPT_PATH)
    classified_matches: list[ClassifiedMatch] = []

    for match in step1_output.entity_matches:
        pair_input = ActivityPairInput(activity_a=match.activity_a, activity_b=match.activity_b)

        result = _call_stage(
            messages=[
                {"role": "system", "content": classify_prompt},
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "activity_a": {"action": "create", "entity": "invoice"},\n'
                        '  "activity_b": {"action": "attach", "entity": "saved invoice"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{\n'
                        '  "activity_a": {"action": "create", "entity": "invoice", "operation_type": "CREATE"},\n'
                        '  "activity_b": {"action": "attach", "entity": "saved invoice", "operation_type": "UPDATE"}\n'
                        '}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "activity_a": {"action": "log out", "entity": "account"},\n'
                        '  "activity_b": {"action": "view", "entity": "account"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{\n'
                        '  "activity_a": {"action": "log out", "entity": "account", "operation_type": "NON_CRUD"},\n'
                        '  "activity_b": {"action": "view", "entity": "account", "operation_type": "READ"}\n'
                        '}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "activity_a": {"action": "log in", "entity": "account"},\n'
                        '  "activity_b": {"action": "reset", "entity": "password"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{\n'
                        '  "activity_a": {"action": "log in", "entity": "account", "operation_type": "READ"},\n'
                        '  "activity_b": {"action": "reset", "entity": "password", "operation_type": "UPDATE"}\n'
                        '}'
                    ),
                },
                {"role": "user", "content": f"Input:\n{pair_input.model_dump_json(indent=2)}"},
            ],
            schema_model=ClassifiedActivityPair,
            model=model
        )

        classified_matches.append(
            ClassifiedMatch(
                activity_a=result.activity_a,
                activity_b=result.activity_b,
                match_type=match.match_type,  # copied through in code, not sent to LLM
            )
        )

    return ClassifiedMatchResult(
        story_a_id=step1_output.story_a_id,
        story_b_id=step1_output.story_b_id,
        classified_matches=classified_matches,
    )

def decide_dependency(step2_output: ClassifiedMatchResult, model: str) -> FoundedDependencyUsingAnnotated:
    decision_prompt = _load_prompt(DECISION_PROMPT_PATH)
    dependencies: list[DependencyEntryAnnotated] = []

    for match in step2_output.classified_matches:
        pair_input = ClassifiedActivityPairInput(
            story_a_id=step2_output.story_a_id,
            story_b_id=step2_output.story_b_id,
            activity_a=match.activity_a,
            activity_b=match.activity_b,
        )

        result = _call_stage(
            messages=[
                {"role": "system", "content": decision_prompt},
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "story_a_id": "US-015",\n'
                        '  "story_b_id": "US-021",\n'
                        '  "activity_a": {"action": "create", "entity": "invoice", "operation_type": "CREATE"},\n'
                        '  "activity_b": {"action": "attach", "entity": "saved invoice", "operation_type": "UPDATE"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": '{"qualifies": true, "prerequisite_id": "US-015", "dependent_id": "US-021"}',
                },
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "story_a_id": "US-017",\n'
                        '  "story_b_id": "US-022",\n'
                        '  "activity_a": {"action": "log out of", "entity": "account", "operation_type": "NON_CRUD"},\n'
                        '  "activity_b": {"action": "view", "entity": "account", "operation_type": "READ"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": '{"qualifies": false, "prerequisite_id": null, "dependent_id": null}',
                },
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "story_a_id": "US-207",\n'
                        '  "story_b_id": "US-042",\n'
                        '  "activity_a": {"action": "review", "entity": "expense report", "operation_type": "READ"},\n'
                        '  "activity_b": {"action": "submit", "entity": "expense report", "operation_type": "CREATE"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": '{"qualifies": true, "prerequisite_id": "US-042", "dependent_id": "US-207"}',
                },
                {
                    "role": "user",
                    "content": (
                        "Input:\n"
                        '{\n'
                        '  "story_a_id": "US-018",\n'
                        '  "story_b_id": "US-025",\n'
                        '  "activity_a": {"action": "view", "entity": "invoice", "operation_type": "READ"},\n'
                        '  "activity_b": {"action": "view", "entity": "invoice", "operation_type": "READ"}\n'
                        '}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": '{"qualifies": false, "prerequisite_id": null, "dependent_id": null}',
                },
                {"role": "user", "content": f"Input:\n{pair_input.model_dump_json(indent=2)}"},
            ],
            schema_model=DependencyVerdict,
            model=model
        )

        if not result.qualifies:
            continue

        prereq_activity = match.activity_a if result.prerequisite_id == step2_output.story_a_id else match.activity_b
        dep_activity = match.activity_b if result.prerequisite_id == step2_output.story_a_id else match.activity_a

        dependencies.append(
            DependencyEntryAnnotated(
                prerequisite_id=result.prerequisite_id,
                dependent_id=result.dependent_id,
                prerequisite_activity=prereq_activity,
                dependent_activity=dep_activity,
                match_type=match.match_type,
            )
        )

    return FoundedDependencyUsingAnnotated(dependencies=dependencies)

VALID_DEPENDENCY_PAIRS = {
    frozenset({"CREATE", "READ"}),
    frozenset({"CREATE", "UPDATE"}),
    frozenset({"CREATE", "DELETE"}),
}


def evaluate_dependency_rule(op_a: str, op_b: str) -> tuple[bool, str | None]:
    if frozenset({op_a, op_b}) not in VALID_DEPENDENCY_PAIRS:
        return False, None

    prereq_side = "a" if op_a == "CREATE" else "b"
    return True, prereq_side


def decide_dependency_nlp(step2_output: ClassifiedMatchResult) -> FoundedDependencyUsingAnnotated:
    dependencies: list[DependencyEntryAnnotated] = []

    for match in step2_output.classified_matches:
        qualifies, prereq_side = evaluate_dependency_rule(
            match.activity_a.operation_type, match.activity_b.operation_type
        )
        if not qualifies:
            continue

        if prereq_side == "a":
            prerequisite_id, dependent_id = step2_output.story_a_id, step2_output.story_b_id
            prereq_activity, dep_activity = match.activity_a, match.activity_b
        else:
            prerequisite_id, dependent_id = step2_output.story_b_id, step2_output.story_a_id
            prereq_activity, dep_activity = match.activity_b, match.activity_a

        dependencies.append(
            DependencyEntryAnnotated(
                prerequisite_id=prerequisite_id,
                dependent_id=dependent_id,
                prerequisite_activity=prereq_activity,
                dependent_activity=dep_activity,
                match_type=match.match_type,
            )
        )

    return FoundedDependencyUsingAnnotated(dependencies=dependencies)


def detect_dependency(story_a: StoryActivity, story_b: StoryActivity, model:str, max_retries: int = 2):
    last_error = None
    for attempt in range(max_retries):
        try:
            step_1 = find_entity_matches(story_a, story_b, model)
            if not step_1.entity_matches:
                print(f"No matches found for pair ({story_a.id}, {story_b.id}). Skipping further analysis.")
                result = AnnotatedDependencyResult(
                    story_a=story_a.Text,
                    story_b=story_b.Text,
                    step_1_match=step_1,
                    step_2_classify=ClassifiedMatchResult(story_a_id=story_a.id, story_b_id=story_b.id, classified_matches=[]),
                    final_llm=FoundedDependencyUsingAnnotated(dependencies=[]),
                    final_nlp=FoundedDependencyUsingAnnotated(dependencies=[])
                )
                return result, False, attempt + 1

            step_2 = classify_activities(step_1, model)
            step_3_llm = decide_dependency(step_2, model)
            step_3_nlp = decide_dependency_nlp(step_2)

            result = AnnotatedDependencyResult(
                story_a=story_a.Text,
                story_b=story_b.Text,
                step_1_match=step_1,
                step_2_classify=step_2,
                final_llm=step_3_llm,
                final_nlp=step_3_nlp
            )

            return result, False, attempt + 1
        except Exception as err:
            last_error = err
            print(f"Warning: attempt {attempt + 1} failed for pair ({story_a.id}, {story_b.id}): {err}")

    print(f"Skipping pair ({story_a.id}, {story_b.id}) after {max_retries} attempts — last error: {last_error}")
    result = AnnotatedDependencyResult(
        story_a=story_a.Text, story_b=story_b.Text,
        step_1_match=EntityMatchResult(story_a_id=story_a.id, story_b_id=story_b.id, entity_matches=[]),
        step_2_classify=ClassifiedMatchResult(story_a_id=story_a.id, story_b_id=story_b.id, classified_matches=[]),
        final_llm=FoundedDependencyUsingAnnotated(dependencies=[]),
        final_nlp=FoundedDependencyUsingAnnotated(dependencies=[])
    )
    return result, True, max_retries




