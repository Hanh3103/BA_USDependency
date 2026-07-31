import time
from stages.annotation import annotate

def test_annotate():
    user_story = (
        "As an agency user, I want the FABS validation rules to accept zero and blank for loan records."
    )
    result = annotate(user_story, "US-001")
    print(result)

if __name__ == '__main__':
    # measure the performance of the model
    start = time.perf_counter()
    test_annotate()
    elapsed = time.perf_counter() - start
    print(f"Elapsed (wall-clock): {elapsed:.4f} seconds")