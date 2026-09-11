from schemas.dependency.dependency_schema import  AnnotatedStory, StoryActivity, AnnotatedDependencyResult, OperationType, ActivityCacheKey
from utils.file_parser import load_annotated_stories
from typing import Optional
from itertools import combinations

from stages.well_formulated_extractor import filter_well_formed

from stages.dependency_analysis_annotated import detect_dependency



def run_dependency_pipeline(data_set_path: str, model:str, pairs: Optional[list[tuple[str, str]]] = None, max_retries: int = 2):
    stories = load_annotated_stories(data_set_path)

    # Step 0: Filter well-formed stories
    kept, dropped = filter_well_formed(stories)
    print(f"Kept {len(kept)} well-formed stories, dropped {len(dropped)} ill-formed stories.")

    kept_ids = {r.id for r in kept}

    for r in dropped:
        print(f"Dropped story {r.Text}: {r.well_formed_reason}")

    story_activities = {
        r.id: StoryActivity(id=r.id, activity=r.activity, Text=r.Text)
        for r in kept
    }

    print(f"Building pairs...")
    if pairs is None:
        pairs = list(combinations(story_activities.keys(), 2))

    print(f"Analyzing {len(pairs)} story pairs for dependencies.")

    results: list[AnnotatedDependencyResult] = []
    failed_pairs: list[tuple[str, str]] = []
    attempts_by_pair: dict[tuple[str, str], int] = {}
    operation_cache:dict[ActivityCacheKey, OperationType] = {}

    for pair in pairs:
        print(f"Analyzing pair: {pair[0]} and {pair[1]}")
        pair_result, failed, attempts_used = detect_dependency(
            story_a=story_activities[pair[0]], story_b=story_activities[pair[1]],
            model=model, operation_cache=operation_cache, max_retries=max_retries
        )
        results.append(pair_result)
        attempts_by_pair[pair] = attempts_used
        if failed:
            failed_pairs.append(pair)

    return results, kept_ids, failed_pairs, attempts_by_pair




if __name__ == '__main__':
    from utils.file_writer import save_results

    input_path = "test/results/annotated_stories.json"
    output_path = f"test/results/result_dependency_annotated.json"

    result_, kept_ids, failed_pairs, attempts_by_pair = run_dependency_pipeline(data_set_path=input_path, model="qwen3:1.7b", pairs=None, max_retries=2)

    save_results(result_, output_path, indent=4)
