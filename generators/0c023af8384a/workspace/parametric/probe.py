"""Run a bounded protected-Racket study for the mirror family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "0c023af8384a"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("_mirror_probe_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _fixed_side_completion(impl, grid, side):
    intermediate = impl.vertical_intermediate(grid)
    h, w = len(intermediate), len(intermediate[0])
    columns = range(0, w // 2) if side == "left" else range((w + 1) // 2, w)
    counts = {
        color: sum(intermediate[r][c] == color for r in range(h) for c in columns)
        for color in range(1, 10)
    }
    selected = min(range(1, 10), key=lambda color: (-counts[color], color))
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] == selected:
                out[r][w - 1 - c] = selected
    return out



def _original_rank_completion(impl, grid, rank):
    counts = {
        color: sum(cell == color for row in grid for cell in row)
        for color in range(1, 10)
    }
    ordered = sorted(range(1, 10), key=lambda color: (-counts[color], color))
    selected = ordered[rank - 1]
    intermediate = impl.vertical_intermediate(grid)
    h, w = len(intermediate), len(intermediate[0])
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] == selected:
                out[r][w - 1 - c] = selected
    return out

def _shortcut_sweep(adapter, seeds=200):
    impl = adapter._impl
    checked_pairs = 0
    for seed in range(seeds):
        episode = adapter.generate(
            seed, {"completion": "vertical_then_selected_horizontal"}, 3, 4
        )
        sides = set()
        raw_frequency_ranks = set()
        left_matches = []
        right_matches = []
        rank_two_matches = []
        rank_three_matches = []
        for pair in episode["train"]:
            grid = pair["input"]
            intermediate = impl.vertical_intermediate(grid)
            selected = impl.selected_color(intermediate)
            columns = [
                c for row in grid for c, cell in enumerate(row) if cell == selected
            ]
            midpoint = len(grid[0]) / 2
            sides.add(
                "left" if sum(columns) / len(columns) < midpoint else "right"
            )
            raw_counts = {
                color: sum(cell == color for row in grid for cell in row)
                for color in range(1, 10)
            }
            raw_order = sorted(
                range(1, 10), key=lambda color: (-raw_counts[color], color)
            )
            raw_frequency_ranks.add(raw_order.index(selected) + 1)
            left_matches.append(
                _fixed_side_completion(impl, grid, "left") == pair["output"]
            )
            right_matches.append(
                _fixed_side_completion(impl, grid, "right") == pair["output"]
            )
            rank_two_matches.append(
                _original_rank_completion(impl, grid, 2) == pair["output"]
            )
            rank_three_matches.append(
                _original_rank_completion(impl, grid, 3) == pair["output"]
            )
            checked_pairs += 1
        if (
            sides != {"left", "right"}
            or raw_frequency_ranks != {2, 3}
            or all(left_matches)
            or all(right_matches)
            or all(rank_two_matches)
            or all(rank_three_matches)
        ):
            raise AssertionError(f"side/frequency shortcut survived seed {seed}")
    return {
        "seeds": seeds,
        "demonstrations_per_seed": 3,
        "checked_pairs": checked_pairs,
        "selected_source_sides": ["left", "right"],
        "selected_raw_frequency_ranks": [2, 3],
        "always_left_rejected": True,
        "always_right_rejected": True,
        "always_rank_two_rejected": True,
        "always_rank_three_rejected": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    contract = json.loads((HOME / "promotion.json").read_text())
    settings = [
        {"completion": "vertical"},
        {"completion": "vertical_then_selected_horizontal"},
    ]
    jobs = [
        {"seed": seed, "settings": setting, "demos": 3, "queries": 4}
        for setting in settings
        for seed in (0, 17)
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    adapter = _load_adapter()
    prefix_checks = []
    for setting in settings:
        full = adapter.generate(29, setting, 3, 4)
        one = adapter.generate(29, setting, 3, 1)
        prefix_checks.append(
            {
                "settings": setting,
                "same_train": full["train"] == one["train"],
                "same_first_query": full["test"][0] == one["test"][0],
            }
        )
    shortcut_sweep = _shortcut_sweep(adapter)
    matched_inputs = []
    for seed in (0, 17):
        a = adapter.generate(seed, settings[0], 3, 4)
        b = adapter.generate(seed, settings[1], 3, 4)
        matched_inputs.append(
            {
                "seed": seed,
                "matched": all(
                    [pair["input"] for pair in a[split]]
                    == [pair["input"] for pair in b[split]]
                    for split in ("train", "test")
                ),
            }
        )
    report = {
        "schema": "arcpuzzles-parametric-focused-study-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "jobs": jobs,
        "racket": result["racket"],
        "racket_evaluations": result["racket_evaluations"],
        "checks": result["checks"],
        "matched_inputs": matched_inputs,
        "prefix_checks": prefix_checks,
        "shortcut_sweep": shortcut_sweep,
        "limits": "Protected Racket: two settings, seeds 0 and 17, three demos and four queries. Python shortcut audit: 200 seeds x three demonstrations.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "out": str(args.out), "racket_evaluations": result["racket_evaluations"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
