import time
from stages.annotation import annotate

def test_annotate():
    user_story = (
        "As a traveler, I want to import a location from a saved TikTok or Instagram video with a single tap, so that I can quickly capture travel inspiration without manually typing details."
    )
    result = annotate(user_story, "US-001")
    print(result)

if __name__ == '__main__':
    # measure the performance of the model
    start = time.perf_counter()
    test_annotate()
    elapsed = time.perf_counter() - start
    print(f"Elapsed (wall-clock): {elapsed:.4f} seconds")