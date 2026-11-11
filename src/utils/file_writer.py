import json
from pathlib import Path
from pydantic import BaseModel

def save_results(results: list[BaseModel] | list[dict], output_path: str, indent: int = 2) -> None:
    """
    Save a list of results to a JSON file.

    Args:
        results: A list of Pydantic BaseModel instances or dictionaries to be saved.
        output_path: The path to the output JSON file.
        indent: The number of spaces to use for indentation in the JSON file (default is 2).

    Returns:
        None
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    serializable = [
        r.model_dump(by_alias=True) if isinstance(r, BaseModel) else r
        for r in results
    ]

    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=indent)

    print(f"Results saved to {output_path}")