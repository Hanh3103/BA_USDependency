from stages.well_formulated_extractor import filter_well_formed
from stages.dependency_analysis_text import detect_dependency_text
from utils.file_parser import load_annotated_stories
from itertools import combinations

def run_dependency_pipeline_text(data_set_path: str, model:str,  pairs=None, max_retries: int = 2):
    """
    Run the dependency analysis pipeline on a dataset of annotated stories using text-based prompts.

    Args:
        data_set_path: The path to the dataset of annotated stories.
        model: The name of the model to use for dependency detection.
        pairs: Optional list of story ID pairs to analyze. If None, all combinations will be analyzed.
        max_retries: The maximum number of retries for the LLM call in case of failure.

    Returns:
        A tuple containing:
            - List of TextDependencyResult: The results of the dependency detection for each pair.
            - Set of kept story IDs: The IDs of well-formed stories that were kept for analysis.
            - List of dropped AnnotatedStory: The stories that were dropped due to being ill-formed.
            - List of failed pairs: The pairs of story IDs for which dependency detection failed
            - Dictionary of attempts by pair: The number of attempts made for each pair.
    """
    stories = load_annotated_stories(data_set_path)
    kept, dropped = filter_well_formed(stories)
    print(f"Kept {len(kept)} well-formed stories, dropped {len(dropped)} ill-formed stories.")

    for r in dropped:
        print(f"Dropped story {r.Text}: {r.well_formed_reason}")

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

    return results, kept_ids, dropped, failed_pairs, attempts_by_pair

if __name__ == '__main__':
    from utils.file_writer import save_results

    input_path = "test/results/annotated_stories.json"
    output_path = "test/results/result_dependency_text.json"
    results, _, failed_pairs, attempts_by_pair = run_dependency_pipeline_text(input_path, model="qwen3:1.7b", pairs=None, max_retries=2)
    save_results(results, output_path, indent=4)