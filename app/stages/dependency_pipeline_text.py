from stages.well_formulated_extractor import filter_well_formed
from stages.dependency_analysis_text import detect_dependency_text
from utils.file_parser import load_annotated_stories
from itertools import combinations

def run_dependency_pipeline_text(data_set_path: str, pairs=None):
    stories = load_annotated_stories(data_set_path)
    kept, dropped = filter_well_formed(stories)
    print(f"Kept {len(kept)} well-formed stories, dropped {len(dropped)} ill-formed stories.")

    kept_ids = {r.id for r in kept}
    story_lookup = {s.id: s for s in stories if s.id in kept_ids}

    if pairs is None:
        pairs = list(combinations(story_lookup.keys(), 2))

    results = []
    for a_id, b_id in pairs:
        print(f"Analyzing pair: {a_id} and {b_id}")
        results.append(detect_dependency_text(story_lookup[a_id], story_lookup[b_id]))
    return results

if __name__ == '__main__':
    from utils.file_writer import save_results

    input_path = "test/results/annotated_stories.json"
    output_path = "test/results/result_dependency_text.json"
    results = run_dependency_pipeline_text(input_path)
    save_results(results, output_path, indent=4)