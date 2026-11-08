"""Prepare exact rank-before-filter interventions from qualified episodes.

The native review_witness command executes and replays both programs. This
stdlib-only recipe builder independently records the intermediate components;
its descriptions remain reviewer-authored, not an execution proof.
Run from WORK/repo.
"""
import argparse
import json
from pathlib import Path

TASK = "a86a630485ac"
DESCRIPTIONS = {
    "step_a": "Find nonzero monochrome 4-connected components and retain those symmetric about their own bounding-box center on the selected axis.",
    "intermediate": "The input-dependent eligible component set with each component's occupied-cell count.",
    "step_b": "Compute the maximum occupied-cell count within that eligible set and paint every eligible component tied at that maximum.",
    "why_b_depends_on_a": "The largest input component can be asymmetric. Ranking all components before applying eligibility sets the wrong maximum and erases valid smaller symmetric winners. Only the ranked-set binding is changed in the counterfactual; classification, tie handling, and painting are preserved. This establishes a conditional-selection dependency, not iterative simulation.",
}


def describe_components(grid, axis):
    """Independent finite flood fill for human-readable intermediate evidence."""
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            seen.add((r, c))
            pending = [(r, c)]
            cells = []
            while pending:
                row, col = pending.pop()
                cells.append((row, col))
                for rr, cc in ((row-1, col), (row+1, col), (row, col-1), (row, col+1)):
                    if (0 <= rr < h and 0 <= cc < w and (rr, cc) not in seen
                            and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        pending.append((rr, cc))
            minr, maxr = min(x[0] for x in cells), max(x[0] for x in cells)
            minc, maxc = min(x[1] for x in cells), max(x[1] for x in cells)
            reflected = {(rr, minc+maxc-cc) if axis == "lr" else (minr+maxr-rr, cc)
                         for rr, cc in cells}
            objects.append({"color": color, "cells": sorted(cells), "size": len(cells),
                            "eligible": reflected == set(cells)})
    return objects


def build(qualification):
    qualification = Path(qualification)
    q = json.loads(qualification.read_text())
    if q["task_id"] != TASK or q["status"] != "qualified":
        raise ValueError("Expected this task's successful native qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    cases = []
    for axis in ("lr", "ud"):
        settings = {"axis": axis, "keep_policy": "largest_eligible"}
        index, episode = next((i, e) for i, e in enumerate(execution["episodes"])
                              if e["settings"] == settings and e["seed"] == 0)
        needle = "(ranked eligible)"
        if episode["program"].count(needle) != 1:
            raise ValueError("Expected one exact eligible ranking-set binding")
        wrong = episode["program"].replace(needle, "(ranked objs)", 1)
        objects = describe_components(episode["train"][0]["input"], axis)
        eligible = [obj for obj in objects if obj["eligible"]]
        eligible_max = max(obj["size"] for obj in eligible)
        global_max = max(obj["size"] for obj in objects)
        if global_max <= eligible_max:
            raise ValueError("The selected case must expose the ranking-order dependency")
        cases.append({
            "episode_index": index, "split": "train", "pair_index": 0,
            "intermediate_value": {
                "axis": axis, "components": objects,
                "eligible_component_maximum": eligible_max,
                "counterfactual_global_maximum": global_max,
                "eligible_winner_count": sum(obj["size"] == eligible_max for obj in eligible),
            },
            "counterfactual_program": wrong, "ablation": "wrong_order",
        })
    return {**DESCRIPTIONS, "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.qualification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"cases": len(result["cases"]), "out": str(args.out), "racket_executed": False}))
