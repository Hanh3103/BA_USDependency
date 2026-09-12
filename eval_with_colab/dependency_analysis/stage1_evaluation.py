import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


ID_WIDTH = 3
POSITIVE_LABELS = {"exact", "semantic"}
LABELS = ["exact", "semantic", "none"]
DEFAULT_GT_LABEL_CANDIDATES = [
    "final_match_type (exact/semantic/none)",
    "human_final_match_type (exact/semantic/none)",
    "gpt5_match_type (exact/semantic/none)",
    "nlp_match_type (exact/semantic/none)",
]


def normalize_id(raw: Any) -> str:
    match = re.search(r"(\d+)", str(raw).strip())

    if not match:
        raise ValueError(f"Cannot normalize story ID: {raw!r}")

    return f"US-{int(match.group(1)):0{ID_WIDTH}d}"


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""

    return " ".join(str(value).strip().casefold().split())


def normalize_label(value: Any) -> str:
    if pd.isna(value):
        return "none"

    label = str(value).strip().casefold()

    if label in POSITIVE_LABELS:
        return label

    return "none"


def row_key(
    story_a_id: Any,
    action_a: Any,
    entity_a: Any,
    story_b_id: Any,
    action_b: Any,
    entity_b: Any,
) -> tuple[str, str, str, str, str, str]:
    return (
        normalize_id(story_a_id),
        normalize_text(action_a),
        normalize_text(entity_a),
        normalize_id(story_b_id),
        normalize_text(action_b),
        normalize_text(entity_b),
    )


def reverse_key(
    key: tuple[str, str, str, str, str, str],
) -> tuple[str, str, str, str, str, str]:
    story_a_id, action_a, entity_a, story_b_id, action_b, entity_b = key
    return (story_b_id, action_b, entity_b, story_a_id, action_a, entity_a)


def choose_gt_label_column(
    ground_truth: pd.DataFrame,
    requested_column: str | None,
) -> str:
    if requested_column:
        if requested_column not in ground_truth.columns:
            raise ValueError(
                f"Requested GT label column not found: {requested_column!r}\n"
                f"Available columns: {list(ground_truth.columns)}"
            )
        return requested_column

    for column in DEFAULT_GT_LABEL_CANDIDATES:
        if column in ground_truth.columns:
            return column

    raise ValueError(
        "Could not find a Stage 1 GT label column. Pass --gt-label-column.\n"
        f"Available columns: {list(ground_truth.columns)}"
    )


def load_stage1_ground_truth(
    path: Path,
    sheet_name: str,
    label_column: str | None,
) -> pd.DataFrame:
    ground_truth = pd.read_excel(path, sheet_name=sheet_name)

    required_columns = {
        "story_a_id",
        "action_a",
        "entity_a",
        "story_b_id",
        "action_b",
        "entity_b",
    }
    missing_columns = required_columns - set(ground_truth.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required B_GT columns: {sorted(missing_columns)}\n"
            f"Available columns: {list(ground_truth.columns)}"
        )

    label_column = choose_gt_label_column(ground_truth, label_column)
    ground_truth = ground_truth.copy()
    ground_truth["gt_match_type"] = ground_truth[label_column].apply(normalize_label)
    ground_truth["gt_positive"] = ground_truth["gt_match_type"].isin(POSITIVE_LABELS)
    ground_truth["key"] = ground_truth.apply(
        lambda row: row_key(
            row["story_a_id"],
            row["action_a"],
            row["entity_a"],
            row["story_b_id"],
            row["action_b"],
            row["entity_b"],
        ),
        axis=1,
    )

    duplicate_keys = ground_truth[ground_truth["key"].duplicated(keep=False)]
    if not duplicate_keys.empty:
        raise ValueError(
            "B_GT contains duplicate Stage 1 keys:\n"
            + duplicate_keys[
                [
                    "story_a_id",
                    "action_a",
                    "entity_a",
                    "story_b_id",
                    "action_b",
                    "entity_b",
                ]
            ].to_string(index=False)
        )

    ground_truth.attrs["label_column"] = label_column
    return ground_truth


def extract_stage1_predictions(
    pipeline_results: list[dict[str, Any]],
    ground_truth_keys: set[tuple[str, str, str, str, str, str]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictions: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for pair_index, pair_result in enumerate(pipeline_results):
        step1 = pair_result.get("step_1_match") or {}
        story_a_id = step1.get("story_a_id") or pair_result.get("story_a_id")
        story_b_id = step1.get("story_b_id") or pair_result.get("story_b_id")

        for match_index, match in enumerate(step1.get("entity_matches") or []):
            activity_a = match.get("activity_a") or {}
            activity_b = match.get("activity_b") or {}
            match_type = normalize_label(match.get("match_type"))

            try:
                key = row_key(
                    story_a_id,
                    activity_a.get("action"),
                    activity_a.get("entity"),
                    story_b_id,
                    activity_b.get("action"),
                    activity_b.get("entity"),
                )
            except ValueError as exc:
                unmatched.append(
                    {
                        "pair_index": pair_index,
                        "match_index": match_index,
                        "reason": str(exc),
                        "raw_match": json.dumps(match, ensure_ascii=False),
                    }
                )
                continue

            if key not in ground_truth_keys and reverse_key(key) in ground_truth_keys:
                key = reverse_key(key)

            record = {
                "key": key,
                "story_a_id": key[0],
                "action_a": activity_a.get("action"),
                "entity_a": activity_a.get("entity"),
                "story_b_id": key[3],
                "action_b": activity_b.get("action"),
                "entity_b": activity_b.get("entity"),
                "predicted_match_type": match_type,
                "explanation": match.get("explanation", ""),
            }

            if key not in ground_truth_keys:
                unmatched.append(
                    {
                        "pair_index": pair_index,
                        "match_index": match_index,
                        "reason": "No matching B_GT row",
                        **{k: v for k, v in record.items() if k != "key"},
                    }
                )
                continue

            if key in predictions:
                previous = predictions[key]
                if previous["predicted_match_type"] != match_type:
                    conflicts.append(
                        {
                            "story_a_id": key[0],
                            "action_a": key[1],
                            "entity_a": key[2],
                            "story_b_id": key[3],
                            "action_b": key[4],
                            "entity_b": key[5],
                            "first_match_type": previous["predicted_match_type"],
                            "conflicting_match_type": match_type,
                        }
                    )
                continue

            predictions[key] = record

    prediction_df = pd.DataFrame(predictions.values())
    conflict_df = pd.DataFrame(conflicts)
    unmatched_df = pd.DataFrame(unmatched)

    return prediction_df, conflict_df, unmatched_df


def prf1(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
    }


def evaluate_stage1(
    predictions: pd.DataFrame,
    ground_truth: pd.DataFrame,
    model_name: str,
    label_column: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if predictions.empty:
        predictions = pd.DataFrame(columns=["key", "predicted_match_type", "explanation"])

    evaluation = ground_truth.merge(
        predictions[["key", "predicted_match_type", "explanation"]],
        how="left",
        on="key",
    )
    evaluation["predicted_match_type"] = evaluation["predicted_match_type"].fillna("none")
    evaluation["pred_positive"] = evaluation["predicted_match_type"].isin(POSITIVE_LABELS)
    evaluation["correct_label"] = (
        evaluation["gt_match_type"] == evaluation["predicted_match_type"]
    )

    tp = int((evaluation["gt_positive"] & evaluation["pred_positive"]).sum())
    fp = int((~evaluation["gt_positive"] & evaluation["pred_positive"]).sum())
    fn = int((evaluation["gt_positive"] & ~evaluation["pred_positive"]).sum())
    tn = int((~evaluation["gt_positive"] & ~evaluation["pred_positive"]).sum())

    binary = prf1(tp, fp, fn)
    accuracy = (tp + tn) / len(evaluation) if len(evaluation) else 0.0

    overall = pd.DataFrame(
        [
            {
                "Model": model_name,
                "GT label column": label_column,
                "B_GT rows": len(evaluation),
                "GT positive rows": int(evaluation["gt_positive"].sum()),
                "Predicted positive rows": int(evaluation["pred_positive"].sum()),
                "TP": binary["TP"],
                "FP": binary["FP"],
                "FN": binary["FN"],
                "TN": tn,
                "Precision": binary["Precision"],
                "Recall": binary["Recall"],
                "F1": binary["F1"],
                "Accuracy": round(accuracy, 4),
            }
        ]
    )

    per_class_rows = []
    for label in LABELS:
        label_tp = int(
            (
                (evaluation["gt_match_type"] == label)
                & (evaluation["predicted_match_type"] == label)
            ).sum()
        )
        label_fp = int(
            (
                (evaluation["gt_match_type"] != label)
                & (evaluation["predicted_match_type"] == label)
            ).sum()
        )
        label_fn = int(
            (
                (evaluation["gt_match_type"] == label)
                & (evaluation["predicted_match_type"] != label)
            ).sum()
        )
        metrics = prf1(label_tp, label_fp, label_fn)
        per_class_rows.append(
            {
                "Model": model_name,
                "Match type": label,
                **metrics,
                "Support": int((evaluation["gt_match_type"] == label).sum()),
            }
        )

    per_class = pd.DataFrame(per_class_rows)
    confusion = pd.crosstab(
        evaluation["gt_match_type"],
        evaluation["predicted_match_type"],
        rownames=["GT"],
        colnames=["Predicted"],
        dropna=False,
    ).reindex(index=LABELS, columns=LABELS, fill_value=0)

    detail_columns = [
        "row_id",
        "story_a_id",
        "action_a",
        "entity_a",
        "story_b_id",
        "action_b",
        "entity_b",
        "gt_match_type",
        "predicted_match_type",
        "correct_label",
        "explanation",
    ]
    details = evaluation[[col for col in detail_columns if col in evaluation.columns]]

    return overall, per_class, confusion, details


def model_name_from_path(path: Path) -> str:
    name = path.stem
    return name.removesuffix("_results")


def evaluate_file(
    prediction_path: Path,
    ground_truth: pd.DataFrame,
    output_dir: Path,
    label_column: str,
) -> pd.DataFrame:
    pipeline_results = json.loads(prediction_path.read_text(encoding="utf-8"))
    model_name = model_name_from_path(prediction_path)
    predictions, conflicts, unmatched = extract_stage1_predictions(
        pipeline_results,
        set(ground_truth["key"]),
    )

    overall, per_class, confusion, details = evaluate_stage1(
        predictions,
        ground_truth,
        model_name,
        label_column,
    )

    safe_model_name = re.sub(r"[^A-Za-z0-9_]+", "_", model_name)
    details.to_csv(output_dir / f"{safe_model_name}_stage1_details.csv", index=False)
    per_class.to_csv(output_dir / f"{safe_model_name}_stage1_per_class.csv", index=False)
    confusion.to_csv(output_dir / f"{safe_model_name}_stage1_confusion_matrix.csv")
    conflicts.to_csv(output_dir / f"{safe_model_name}_stage1_conflicts.csv", index=False)
    unmatched.to_csv(
        output_dir / f"{safe_model_name}_stage1_unmatched_predictions.csv",
        index=False,
    )

    print(f"\n{model_name}")
    print(overall.to_string(index=False))
    print("\nConfusion matrix:")
    print(confusion.to_string())

    if not conflicts.empty:
        print(f"Conflicting duplicate predictions: {len(conflicts)}")
    if not unmatched.empty:
        print(f"Unmatched predictions: {len(unmatched)}")

    return overall


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Stage 1 entity matching against the B_GT sheet."
    )
    parser.add_argument(
        "--gt-path",
        type=Path,
        default=Path("baseline/Ground_truth_OBD_dependency.xlsx"),
        help="Path to the Excel workbook containing B_GT.",
    )
    parser.add_argument(
        "--gt-sheet",
        default="B_GT",
        help="Ground-truth sheet name.",
    )
    parser.add_argument(
        "--gt-label-column",
        default=None,
        help="B_GT label column to evaluate. Auto-detected when omitted.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        nargs="+",
        default=None,
        help="One or more pipeline *_results.json files. Defaults to pipeline_outputs/*_results.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_outputs/stage1"),
        help="Directory for evaluation CSV outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prediction_paths = args.predictions
    if prediction_paths is None:
        prediction_paths = sorted(Path("pipeline_outputs").glob("*_results.json"))

    if not prediction_paths:
        raise FileNotFoundError("No prediction result files found.")

    ground_truth = load_stage1_ground_truth(
        args.gt_path,
        args.gt_sheet,
        args.gt_label_column,
    )
    label_column = ground_truth.attrs["label_column"]

    print(f"Ground truth: {args.gt_path}")
    print(f"Sheet: {args.gt_sheet}")
    print(f"GT label column: {label_column}")
    print(f"B_GT rows: {len(ground_truth)}")
    print(f"Output directory: {args.output_dir}")

    summary_frames = []
    for prediction_path in prediction_paths:
        summary_frames.append(
            evaluate_file(
                prediction_path,
                ground_truth,
                args.output_dir,
                label_column,
            )
        )

    summary = pd.concat(summary_frames, ignore_index=True)
    summary.to_csv(args.output_dir / "stage1_summary_all_models.csv", index=False)

    print(f"\nSaved summary: {args.output_dir / 'stage1_summary_all_models.csv'}")


if __name__ == "__main__":
    main()
