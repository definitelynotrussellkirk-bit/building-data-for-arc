#!/usr/bin/env python3
"""Source-bound audit probe for a public-profile memorization shortcut."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "e9b415370025"


def background_of(grid: list[list[int]]) -> int:
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    maximum = max(counts.values())
    return next(value for value in flat if counts[value] == maximum)


def render_profile(grid: list[list[int]], height_count: int, width_count: int) -> list[list[int]]:
    background = background_of(grid)
    output = [[background for _ in range(16)] for _ in range(16)]
    top = 16 - height_count
    for index in range(height_count):
        row = top + index
        for col in range(width_count):
            output[row][col] = 2
        offset = width_count - height_count + index
        left = min(offset, width_count - 1 - offset)
        right = width_count - 1 - left
        output[row][left] = 4
        output[row][right] = 4
    return output


def public_profile_memorizer(grid: list[list[int]]) -> list[list[int]]:
    """Fit the three public pairs using only canvas size and presence of color 0."""
    if len(grid) == 15 and len(grid[0]) == 15:
        return render_profile(grid, 5, 7)
    if len(grid) == 16 and len(grid[0]) == 16:
        return render_profile(grid, 12, 14) if any(0 in row for row in grid) else render_profile(grid, 5, 10)
    raise ValueError("shortcut only covers the public 15x15/16x16 canvases")


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_checks = []
    for pair in canonical:
        predicted = public_profile_memorizer(pair["input"])
        canonical_checks.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "matched": predicted == pair["output"],
            }
        )

    counterexample = None
    for seed in range(20_000, 30_000):
        grid = generator.generate(seed, seed * 17 + 3, difficulty="easy", scene_profile="generalized")
        if len(grid) != 16 or any(0 in row for row in grid):
            continue
        intended = generator.rule_mirror(grid)
        rival = public_profile_memorizer(grid)
        if intended != rival:
            analysis = generator._analyze_scene(grid)
            counterexample = {
                "seed": seed,
                "sample_index": seed * 17 + 3,
                "difficulty": "easy",
                "overrides": {"scene_profile": "generalized"},
                "observed_overrides": generator.observe_overrides(grid),
                "analysis": analysis,
                "input": grid,
                "intended_output_python_mirror": intended,
                "rival_output": rival,
            }
            break
    if counterexample is None:
        raise RuntimeError("no generated counterexample found")

    invalid_sample = {"sample_index": -1}
    try:
        grid = generator.generate(17, -1, difficulty="hard")
    except Exception as exc:
        invalid_sample.update({"status": "rejected", "exception": repr(exc)})
    else:
        invalid_sample.update(
            {
                "status": "accepted_invalid_scalar",
                "grid": grid,
                "self_check": generator.self_check(grid),
            }
        )

    report = {
        "schema": "arcpuzzles-audit-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "shortcut": (
            "15x15 -> public H5/W7; 16x16 with any color-0 cell -> public H12/W14; "
            "other 16x16 -> public H5/W10"
        ),
        "canonical_checks": canonical_checks,
        "canonical_matched": sum(row["matched"] for row in canonical_checks),
        "canonical_total": len(canonical_checks),
        "counterexample": counterexample,
        "invalid_sample_index_probe": invalid_sample,
    }
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    racket_input = Path(__file__).with_name("e9b415370025-shortcut-input.json")
    racket_input.write_text(json.dumps({"input": counterexample["input"]}, indent=2) + "\n", encoding="utf-8")
    print(out)
    print(racket_input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
