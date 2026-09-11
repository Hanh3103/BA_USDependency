from stages.well_formulated_extractor import filter_well_formed
from stages.dependency_analysis_text import detect_dependency_text
from utils.file_parser import load_annotated_stories
from itertools import combinations

def run_dependency_pipeline_text(data_set_path: str, model:str,  pairs=None, max_retries: int = 2):
    stories = load_annotated_stories(data_set_path)
    kept, dropped = filter_well_formed(stories)
    print(f"Kept {len(kept)} well-formed stories, dropped {len(dropped)} ill-formed stories.")

    kept_ids = {r.id for r in kept}
    story_lookup = {s.id: s for s in stories if s.id in kept_ids}

    if pairs is None:
        pairs = list(combinations(story_lookup.keys(), 2))

    results = []
    failed_pairs = []
    attempts_by_pair = {}

    for a_id, b_id in pairs:
        print(f"Analyzing pair: {a_id} and {b_id}")
        result, failed, attempts_used = detect_dependency_text(
            story_lookup[a_id], story_lookup[b_id], model=model, max_retries=max_retries
        )
        results.append(result)
        attempts_by_pair[(a_id, b_id)] = attempts_used
        if failed:
            failed_pairs.append((a_id, b_id))

    return results, kept_ids, failed_pairs, attempts_by_pair

if __name__ == '__main__':
    from utils.file_writer import save_results

    input_path = "test/results/annotated_stories.json"
    output_path = "test/results/result_dependency_text.json"
    results, _, failed_pairs, attempts_by_pair = run_dependency_pipeline_text(input_path, model="qwen3:1.7b", pairs=None, max_retries=2)
    save_results(results, output_path, indent=4)