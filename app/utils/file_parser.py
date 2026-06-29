import json
from pathlib import Path
import re


def remove_leading_numbering(line: str) -> str:
    cleaned_line = re.sub(r"^#\w+#s*", "", line)  # remove leading #...# and any whitespace
    raise ValueError("Line is empty after removing leading numbering") if not cleaned_line else cleaned_line


def load_stories(path: str) -> list[str]:
    p = Path(path) 

    if not p.exists():
        raise FileNotFoundError(f"File not found at: {path}")
    
    if p.suffix == ".json":
        with open(p, "r") as f:
            raw_data = json.load(f)
        
        if isinstance(raw_data, list): # check if the loaded data is a list
            if all(isinstance(item, str) for item in raw_data): # check if all items in the list are strings
                return raw_data
            
            if all(isinstance(item, dict) and "Text" in item for item in raw_data): # check if all items are dicts with a "Text" key
                return [item["Text"] for item in raw_data]
            
        raise ValueError("JSON file must contain a list of strings or a list of dicts with a 'Text' key.")

    elif p.suffix == ".txt":
        with open(p, "r") as f:
            lines = f.readlines()
        
        stories = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^#\w+#\s*", "", line)
            if cleaned:
                stories.append(cleaned)
        
        if not stories:
            content = f.read()
            stories = [story.strip() for story in content.split("\n") if story.strip()]
        
        if not stories:
            raise ValueError("Text file is empty or contains only whitespace.")
        return stories
    else:
        raise ValueError("Unsupported file format. Please provide a .json or .txt file.")



if __name__ == "__main__":
    import sys

    project_root = Path(__file__).parent.parent

    print("Input options:")
    print("  1 — Choose from available files")
    print("  2 — Enter complete path")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "1":
        files = (
            list(project_root.rglob("*.txt")) +
            list(project_root.rglob("*.json"))
        )

        # exclude irrelevant json files
        files = [
            f for f in files
            if not any(part in f.parts for part in
                       {"node_modules", "__pycache__", ".venv", "prompts"})
        ]

        if not files:
            print("No .txt or .json files found in project")
        else:
            print("\nAvailable files:")
            for i, f in enumerate(files):
                print(f"  {i+1} — {f.relative_to(project_root)}")

            pick = input("\nEnter number: ").strip()
            try:
                path = files[int(pick) - 1]
            except (ValueError, IndexError):
                print("Invalid selection")
                exit(1)

    # ── option 2: complete path ──
    elif choice == "2":
        raw = input("Enter complete path: ").strip()
        path = Path(raw)
        if not path.is_absolute():
            path = project_root / path

    else:
        print("Invalid choice — enter 1 or 2")
        exit(1)

    # ── load and display ──
    try:
        stories = load_stories(str(path))
        print(f"\nLoaded {len(stories)} stories from: {path}\n")
        for i, story in enumerate(stories):
            print(f"US-{i+1:02d}: {story}\n")
    except Exception as e:
        print(f"Error: {e}")