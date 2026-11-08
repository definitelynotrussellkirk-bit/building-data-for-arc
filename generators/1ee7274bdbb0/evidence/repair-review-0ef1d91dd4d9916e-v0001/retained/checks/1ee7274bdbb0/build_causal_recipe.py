"""Select qualified tile cases and swap rotation/settling in the exact programs.

Intermediate descriptions are authored metadata; review_witness performs the
protected-Racket execution and replay. Run from WORK/repo.
"""
import argparse
import json
from pathlib import Path

TASK = "1ee7274bdbb0"
DESCRIPTIONS = {
    "step_a": "Use marker presence to turn each complete tile motif clockwise or counterclockwise, leaving unmarked motifs unturned.",
    "intermediate": "Each tile's transformed occupied-cell set, before vertical translation.",
    "step_b": "Compute the lowest occupied row of that transformed set and move all its cells down by one common displacement until it touches the tile's bottom edge.",
    "why_b_depends_on_a": "Rotation changes the occupied rows from which the settling displacement is calculated. Swapping only settling and the marker-selected quarter-turn changes final positions while retaining the same predicate, motif, turn and settling function. Disconnected parts remain rigid; this is a geometric state dependency, with no iterative-simulation or training-gain claim.",
}


def intermediates(grid, turn):
    h, w = len(grid), len(grid[0])
    divider_rows = [r for r in range(h) if all(value == 9 for value in grid[r])]
    divider_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    row_edges, col_edges = [-1, *divider_rows, h], [-1, *divider_cols, w]
    result = []
    for r0, r1 in zip(row_edges, row_edges[1:]):
        for c0, c1 in zip(col_edges, col_edges[1:]):
            size = r1 - r0 - 1
            assert size == c1 - c0 - 1
            motif = {(r, c) for r in range(size) for c in range(size)
                     if grid[r0 + 1 + r][c0 + 1 + c] == 2}
            markers = {(r, c) for r in range(size) for c in range(size)
                       if grid[r0 + 1 + r][c0 + 1 + c] == 3}
            turned = set(motif)
            if markers:
                turned = ({(c, size - 1 - r) for r, c in motif} if turn == "cw"
                          else {(size - 1 - c, r) for r, c in motif})
            drop = size - 1 - max(r for r, c in turned) if turned else 0
            raw_drop = size - 1 - max(r for r, c in motif) if motif else 0
            result.append({
                "tile_origin": [r0 + 1, c0 + 1], "tile_size": size,
                "raw_motif": sorted(motif), "markers": sorted(markers),
                "transformed_occupied_cells": sorted(turned),
                "correct_post_turn_drop": drop,
                "counterfactual_pre_turn_drop": raw_drop,
            })
    return result


def build(qualification):
    qualification = Path(qualification)
    report = json.loads(qualification.read_text())
    if report["task_id"] != TASK or report["status"] != "qualified":
        raise ValueError("Expected this family's successful qualification")
    execution = json.loads(qualification.with_name("execution.json").read_text())
    cases = []
    for turn, pair_index in (("cw", 0), ("ccw", 1)):
        index, episode = next((i, episode) for i, episode in enumerate(execution["episodes"])
                              if episode["settings"] == {"turn": turn, "post": "settle_down"}
                              and episode["seed"] == 0)
        program = episode["program"]
        correct = f"(settle-down (if (> (count-color t 3) 0) (rotate-{turn} tile) tile))"
        wrong_order = (f"(if (> (count-color t 3) 0) (rotate-{turn} (settle-down tile)) "
                       "(settle-down tile))")
        if program.count(correct) != 1:
            raise ValueError("Expected exactly one qualified turn-then-settle action")
        grid = episode["train"][pair_index]["input"]
        cases.append({"episode_index": index, "split": "train", "pair_index": pair_index,
                      "intermediate_value": {"tiles": intermediates(grid, turn)},
                      "counterfactual_program": program.replace(correct, wrong_order, 1),
                      "ablation": "wrong_order"})
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
    print(json.dumps({"cases": len(result["cases"]), "racket_executed": False,
                      "out": str(args.out)}))
