import pandas as pd
from typing import Any, Dict, List, Tuple
from pathlib import Path
import json
import re

ID_WIDTH = 3  # Adjust this as needed for your ID format

def normalize_id(raw) -> str:
    """Turn 'US_1', 'US-1', 'US-001', 1, etc. into a canonical 'US-001' form."""
    s = str(raw).strip()
    m = re.search(r"(\d+)", s)
    if not m:
        raise ValueError(f"Could not extract a story number from id: {raw!r}")
    num = int(m.group(1))
    return f"US-{num:0{ID_WIDTH}d}"


def load_gt_text_map(path: str, sheet_name: str = "USs") -> Dict[str, str]:
    """Reads the GT Excel's 'USs' sheet (US_ID, US_Text columns) -- the authoritative
    ID<->text mapping, independent of the OBD_Matrix dependency grid. Returns
    {normalized_id: text}, e.g. {'US-001': 'As a new user, ...'}.
    """
    df = pd.read_excel(path, sheet_name=sheet_name, header=0)

    required_cols = {"US_ID", "US_Text"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Expected columns {required_cols} in sheet {sheet_name!r}, got {list(df.columns)}")

    if df["US_ID"].isna().any() or df["US_Text"].isna().any():
        bad_rows = df[df["US_ID"].isna() | df["US_Text"].isna()]
        raise ValueError(f"Found null US_ID/US_Text rows in {sheet_name!r}:\n{bad_rows}")

    story_map: Dict[str, str] = {}
    for _, row in df.iterrows():
        story_id = normalize_id(row["US_ID"])
        if story_id in story_map:
            raise ValueError(f"Duplicate US_ID {story_id!r} in {sheet_name!r} sheet of {path}")
        story_map[story_id] = str(row["US_Text"])

    return story_map

from src.utils.file_parser import load_annotated_stories  # the actual function used by your pipeline
from src.schemas.dependency.dependency_schema import AnnotatedStory  # the actual AnnotatedStory class used by your pipeline

def _get_story_text(story: "AnnotatedStory") -> str:
    """AnnotatedStory's text field is 'Text' per the JSON schema; fall back to
    lowercase 'text' just in case the pydantic field name differs from the JSON key."""
    for attr in ("Text", "text"):
        if hasattr(story, attr):
            return getattr(story, attr)
    raise AttributeError(
        f"AnnotatedStory has neither 'Text' nor 'text' attribute. "
        f"Available fields: {list(story.model_fields.keys())}"
    )

def _normalize_text(s: str) -> str:
    """Collapse whitespace and casing so trivial formatting differences (extra spaces,
    line breaks, capitalization) don't cause a false text mismatch between two files."""
    return re.sub(r"\s+", " ", str(s).strip()).casefold()


def check_id_consistency_by_text(
    gt_stories: Dict[str, str],
    other_path: str,
    label: str = "dataset",
    raise_on_mismatch: bool = True,
) -> Dict[str, Any]:
    """Loads stories via the pipeline's own load_annotated_stories (so this test exercises
    the exact ID-assignment logic used in production), matches them against the GT text
    map by TEXT content, and checks that matched stories carry the exact same ID.
    """
    other_story_objs = load_annotated_stories(other_path)

    other_stories: Dict[str, str] = {}
    for story in other_story_objs:
        story_id = story.id
        text = _get_story_text(story)
        if story_id in other_stories:
            raise ValueError(f"Duplicate story id {story_id!r} in {other_path} (collides with an earlier story).")
        other_stories[story_id] = text

    gt_by_norm_text = {_normalize_text(t): (sid, t) for sid, t in gt_stories.items()}
    other_by_norm_text = {_normalize_text(t): (sid, t) for sid, t in other_stories.items()}

    common_text = set(gt_by_norm_text) & set(other_by_norm_text)
    only_in_gt = set(gt_by_norm_text) - set(other_by_norm_text)
    only_in_other = set(other_by_norm_text) - set(gt_by_norm_text)

    id_mismatches = []  # same text, different id
    for nt in sorted(common_text):
        gt_id, gt_text = gt_by_norm_text[nt]
        other_id, _ = other_by_norm_text[nt]
        if gt_id != other_id:
            id_mismatches.append({"text": gt_text, "gt_id": gt_id, "other_id": other_id})

    report = {
        "label": label,
        "other_path": other_path,
        "n_gt_stories": len(gt_stories),
        "n_other_stories": len(other_stories),
        "n_common_texts": len(common_text),
        "texts_only_in_gt": [gt_by_norm_text[nt][1] for nt in sorted(only_in_gt)],
        "texts_only_in_other": [other_by_norm_text[nt][1] for nt in sorted(only_in_other)],
        "id_mismatches": id_mismatches,
        "is_consistent": not id_mismatches and not only_in_gt and not only_in_other,
    }

    if report["is_consistent"]:
        print(f"[{label}] OK: {len(common_text)} stories match by text with identical IDs")
    else:
        print(f"[{label}] MISMATCH between GT and {other_path}")
        if id_mismatches:
            print(f"  {len(id_mismatches)} stories have the SAME text but DIFFERENT IDs:")
            for m in id_mismatches:
                print(f"    gt_id={m['gt_id']!r} vs other_id={m['other_id']!r} :: {m['text'][:80]!r}")
        if only_in_gt:
            print(f"  {len(only_in_gt)} story text(s) in GT not found in {other_path}")
        if only_in_other:
            print(f"  {len(only_in_other)} story text(s) in {other_path} not found in GT")
        if raise_on_mismatch:
            raise AssertionError(f"Story text/ID mismatch for {label}; see printed report.")

    return report

if __name__ == '__main__':
    gt_excel_path = "/eval_with_colab/dependency_analysis/baseline/Ground_truth_OBD_dependency.xlsx"
    gt_stories = load_gt_text_map(gt_excel_path, sheet_name="USs")

    other_json_path = "/eval_with_colab/annotation/baseline/20US_baseline.json"

    report = check_id_consistency_by_text(gt_stories, other_json_path, label="annotated_stories.json", raise_on_mismatch=False)

    print("=== Only in GT (Excel) ===")
    for t in report["texts_only_in_gt"]:
        print(repr(t))
        print()

    print("=== Only in JSON ===")
    for t in report["texts_only_in_other"]:
        print(repr(t))
        print()