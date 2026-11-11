from schemas.dependency.dependency_schema import  AnnotatedStory, StoryActivity, PairResult
from utils.file_parser import load_annotated_stories
from typing import Optional
from itertools import combinations

from stages.well_formulated_extractor import filter_well_formed
from stages.taxonomy import collect_distinct_verbs, build_verb_taxonomy

from stages.dependency_analysis_annotated import detect_dependency
import json



def run_dependency_pipeline(data_set_path: str, pairs: Optional[list[tuple[str, str]]] = None) -> list[PairResult]:
    stories = load_annotated_stories(data_set_path)

    # Step 0: Filter well-formed stories
    kept, dropped = filter_well_formed(stories)
    print(f"Kept {len(kept)} well-formed stories, dropped {len(dropped)} ill-formed stories.")

    for r in dropped:
        print(f"Dropped story {r.Text}: {r.well_formed_reason}")

    #Step 1: Taxonomy
    story_activities = {
        r.id: StoryActivity(id=r.id, activity=r.activity, Text=r.Text)
        for r in kept
    }

    distinct_verbs = collect_distinct_verbs(list(story_activities.values()))
    print(f"Collected {len(distinct_verbs)} distinct verbs from well-formed stories.")

    print(f"Building verb taxonomy...")
    taxonomy = build_verb_taxonomy(distinct_verbs)

    print(f"Building pairs...")
    if pairs is None:
        pairs = list(combinations(story_activities.keys(), 2))

    print(f"Analyzing {len(pairs)} story pairs for dependencies.")

    results: list[PairResult] = []

    for pair in pairs:
        print(f"Analyzing pair: {pair[0]} and {pair[1]}")
        pair_result= detect_dependency(story_a=story_activities[pair[0]],story_b=story_activities[pair[1]], taxonomy=taxonomy)
        results.append(pair_result)

    return results

def save_results(result: list[PairResult], path: str):
    with open(path, "w") as f:
        json.dump([r.model_dump(by_alias=True) for r in result], f, indent=4)
    print(f"Results saved to {path}")


if __name__ == '__main__':
    input_path = "test/results/annotated_stories.json"
    output_path = f"test/results/result_dependency.json"

    result_ = run_dependency_pipeline(data_set_path=input_path)

    save_results(result_, output_path)
