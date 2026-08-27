from schemas.dependency.dependency_schema import  AnnotatedStory, StoryActivity, AnnotatedDependencyResult
from utils.file_parser import load_annotated_stories
from typing import Optional
from itertools import combinations

from stages.well_formulated_extractor import filter_well_formed

from stages.dependency_analysis_annotated import detect_dependency



def run_dependency_pipeline(data_set_path: str, model:str, pairs: Optional[list[tuple[str, str]]] = None) :
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

    for pair in pairs:
        print(f"Analyzing pair: {pair[0]} and {pair[1]}")
        pair_result= detect_dependency(story_a=story_activities[pair[0]],story_b=story_activities[pair[1]], model=model)
        results.append(pair_result)

    return results, kept_ids



if __name__ == '__main__':
    from utils.file_writer import save_results

    input_path = "test/results/annotated_stories.json"
    output_path = f"test/results/result_dependency_annotated.json"

    result_, _ = run_dependency_pipeline(data_set_path=input_path, model="qwen3:1.7b", pairs=None)

    save_results(result_, output_path, indent=4)
