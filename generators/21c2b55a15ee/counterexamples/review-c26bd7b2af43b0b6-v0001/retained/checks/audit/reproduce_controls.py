from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


def nonzero_colors(grid):
    return sorted({v for row in grid for v in row if v != 0})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", choices=("702934c31043", "21c2b55a15ee"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    module, source, digest = load_selected_generator(args.task_id, root=root)
    seed = 42
    sample_index = 7
    difficulty = "medium"

    if args.task_id == "702934c31043":
        override_name = "rectangle_count"
        low, high = 1, 6
        manual = [[0] * 6 for _ in range(6)]
        manual[1][1] = manual[1][2] = manual[1][3] = 4
        manual_description = (
            "Three collinear cells of one color are not three corners of an "
            "axis-aligned rectangle, but self_check accepts them."
        )
    else:
        override_name = "n_components"
        low, high = 1, 5
        manual = [[0] * 7 for _ in range(7)]
        manual[1][1] = manual[1][2] = manual[2][1] = 2
        manual[4][4] = manual[4][5] = manual[5][4] = 3
        manual[6][0] = 2  # second disconnected component reuses color 2
        manual_description = (
            "Two disconnected components reuse color 2, contrary to the "
            "declared distinct-color-per-component invariant, but self_check "
            "only counts colors and accepts the grid."
        )

    low_grid = module.generate(seed, sample_index, difficulty=difficulty, **{override_name: low})
    high_grid = module.generate(seed, sample_index, difficulty=difficulty, **{override_name: high})
    report = {
        "schema": "arcpuzzles-adversarial-audit-reproducer-v1",
        "task_id": args.task_id,
        "selected_source": str(source.relative_to(root)),
        "generator_sha256": digest,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "override_probe": {
            "name": override_name,
            "low": low,
            "high": high,
            "low_input": low_grid,
            "high_input": high_grid,
            "identical_inputs": low_grid == high_grid,
            "low_self_check": module.self_check(low_grid, difficulty=difficulty),
            "high_self_check": module.self_check(high_grid, difficulty=difficulty),
            "low_nonzero_colors": nonzero_colors(low_grid),
            "high_nonzero_colors": nonzero_colors(high_grid),
        },
        "validator_probe": {
            "description": manual_description,
            "input": manual,
            "self_check": module.self_check(manual, difficulty=difficulty),
            "nonzero_colors": nonzero_colors(manual),
        },
        "limits": (
            "Focused source-bound override and validator probe only; it does "
            "not assess Racket label correctness or lesson identifiability."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": args.task_id,
        "generator_sha256": digest,
        "override": override_name,
        "identical_inputs": low_grid == high_grid,
        "validator_self_check": report["validator_probe"]["self_check"],
    }, indent=2))


if __name__ == "__main__":
    main()
