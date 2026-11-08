from __future__ import annotations

from collections import deque
from copy import deepcopy
from pathlib import Path
import argparse
import json
import sys

TASK_ID = "01dfed2930fa"
SOURCE_ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(SOURCE_ROOT / "shared/runtime"))

from reviewer_support import load_selected_generator


def rooms(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 8 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 8 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def first_seed_rival(grid):
    output = deepcopy(grid)
    for cells in rooms(grid):
        first_color = next((grid[r][c] for r, c in sorted(cells) if grid[r][c] not in (0, 8)), None)
        if first_color is not None:
            for r, c in cells:
                output[r][c] = first_color
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator, source, source_hash = load_selected_generator(TASK_ID, root=SOURCE_ROOT)
    indices = [4, 5, 6, 7]
    generated = [generator.generate(0, i, difficulty="easy") for i in indices]
    racket = json.loads(args.racket.read_text())
    outputs = [entry["output"] for entry in racket["results"]]
    rivals = [first_seed_rival(grid) for grid in generated]
    room_stats = []
    for grid in generated:
        stats = []
        for cells in rooms(grid):
            colors = sorted({grid[r][c] for r, c in cells if grid[r][c] not in (0, 8)})
            stats.append({"seed_colors": colors, "seed_cells": sum(grid[r][c] not in (0, 8) for r, c in cells)})
        room_stats.append(stats)

    report = {
        "schema": "audit-counterexample-current-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(SOURCE_ROOT)),
        "generator_sha256": source_hash,
        "executed_rule_hash": racket["executed_rule_hash"],
        "seed": 0,
        "difficulty": "easy",
        "sample_indices": indices,
        "generated_inputs_match_apply_inputs": [
            generated[i] == json.loads((Path(__file__).with_name("inputs.json")).read_text())["inputs"][i]
            for i in range(4)
        ],
        "self_check_errors": [generator.self_check(grid, difficulty="easy") for grid in generated],
        "room_stats": room_stats,
        "rival_matches": [rival == output for rival, output in zip(rivals, outputs)],
        "finding": (
            "The first-seed rival matches all three demonstrations at indices 4,5,6, "
            "but differs on query index 7 because that input contains a two-color room."
        ),
        "inputs": generated,
        "racket_outputs": outputs,
        "rival_outputs": rivals,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": source_hash,
        "self_check_errors": report["self_check_errors"],
        "rival_matches": report["rival_matches"],
        "generated_inputs_match_apply_inputs": report["generated_inputs_match_apply_inputs"],
    }, indent=2))
    return 0 if report["rival_matches"] == [True, True, True, False] and all(not e for e in report["self_check_errors"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
