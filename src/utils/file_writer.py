import json
from pathlib import Path
from pydantic import BaseModel

def save_results(results: list[BaseModel] | list[dict], output_path: str, indent: int = 2) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    serializable = [
        r.model_dump(by_alias=True) if isinstance(r, BaseModel) else r
        for r in results
    ]

    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=indent)

    print(f"Results saved to {output_path}")