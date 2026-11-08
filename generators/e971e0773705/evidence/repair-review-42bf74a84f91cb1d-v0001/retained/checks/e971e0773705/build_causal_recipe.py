"""Author cancellation witnesses from exact native-qualified pairs.

The existing arcpuzzles.review_witness build command independently executes
and replays the selected reference and counterfactual programs afterward.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


TASK = "e971e0773705"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    qualified = json.loads(args.qualification.read_bytes())
    execution_path = args.qualification.with_name("execution.json")
    if qualified.get("status") != "qualified" or qualified.get("task_id") != TASK:
        raise ValueError("Expected this task's native qualified receipt")
    expected = {"path": "execution.json", "sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest()}
    if qualified.get("execution") != expected:
        raise ValueError("Execution file does not match qualification")
    execution = json.loads(execution_path.read_bytes())
    root = Path(__file__).resolve().parents[2] / "repo"
    path = root / "generators" / TASK / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_tally_causal_recipe", path)
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    settings = {"count_mode": "cancel_opposites"}
    candidates = [(i, episode) for i, episode in enumerate(execution["episodes"])
                  if episode["settings"] == settings]
    selected = []
    for index, episode in candidates:
        if episode["program"] != prototype.program(settings):
            raise ValueError("Qualified cancellation program differs from current source")
        for pair_index, pair in enumerate(episode["train"]):
            top, bottom = prototype.counts(pair["input"])
            common = min(top, bottom)
            correct = (min(4, top - common), min(4, bottom - common))
            capped = (min(4, top), min(4, bottom))
            wrong = (capped[0] - min(capped), capped[1] - min(capped))
            if correct != wrong:
                selected.append((index, "train", pair_index, "wrong_order"))
                break
        if selected:
            break
    for index, episode in candidates:
        for pair_index, pair in enumerate(episode["test"]):
            grid = pair["input"]
            top, bottom = prototype.counts(grid)
            if len(grid) == len(grid[0]) == 30 and min(top, bottom) > 0:
                selected.append((index, "test", pair_index, "skip_a"))
                break
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise ValueError("Qualification lacks a noncommuting demo or dense30x30 cancellation query")
    recipe = {
        "step_a": "Find the isolated red four-connected T components, classify their orientation, and cancel one top-bar T against one bottom-bar T until one orientation has no unmatched objects.",
        "intermediate": "The input-dependent top/bottom component census, matched-pair count min(top,bottom), and the two uncapped unmatched-object counts after cancellation.",
        "step_b": "Cap each unmatched-object count at four and use the capped counts to select the fixed blue and green tally positions in the 3x6 emblem.",
        "why_b_depends_on_a": "The tally cannot be chosen from the original counts or their capped values: cancellation changes the counts that B must encode, and capping too early loses information about their difference. One witness reverses cancellation and capping; another skips cancellation on a dense30x30 scene. This is a count-state dependency, not a claim of spatial matching or iterative grid motion.",
        "cases": [],
    }
    for index, split, pair_index, ablation in selected:
        pair = execution["episodes"][index][split][pair_index]
        top, bottom = prototype.counts(pair["input"])
        matched = min(top, bottom)
        residual = (top - matched, bottom - matched)
        capped_original = (min(4, top), min(4, bottom))
        wrong = (capped_original[0] - min(capped_original), capped_original[1] - min(capped_original))
        program = (prototype.rule_program("cancel_opposites", cap_before_cancel=True)
                   if ablation == "wrong_order" else prototype.program({"count_mode": "raw"}))
        if prototype.solve(pair["input"], count_mode="cancel_opposites") != pair["output"]:
            raise ValueError("Authored count interpretation disagrees with qualified output")
        recipe["cases"].append({
            "episode_index": index, "split": split, "pair_index": pair_index,
            "ablation": ablation, "counterfactual_program": program,
            "intermediate_value": {
                "top_bar_count": top, "bottom_bar_count": bottom,
                "matched_opposite_pairs": matched, "uncapped_residual_counts": residual,
                "capped_residual_counts": tuple(min(4, count) for count in residual),
                "original_counts_capped_too_early": capped_original,
                "cap_before_cancel_result": wrong,
                "active_input_cells": sum(value != 0 for row in pair["input"] for value in row),
            },
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(recipe, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": "authored_recipe", "cases": 2, "out": str(args.out)}))


if __name__ == "__main__":
    main()
