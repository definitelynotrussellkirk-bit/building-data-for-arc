"""Independent probes for ARC task 302ddfbe2baa.

This module intentionally does not import helper functions from the selected
generator when defining the rule oracle or scene measurements.  It gives future
reviewers one portable place to replay canonical pairs, audit named rivals, and
inspect cyclic lesson windows.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

from reviewer_support import canonical_pairs as _canonical_pairs
from reviewer_support import find_root

TASK_ID = "302ddfbe2baa"
TASK_DIR = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_DIR / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_probe", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return list(_canonical_pairs(TASK_ID, root=find_root(__file__)))


def _shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty row sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def positions(grid: Sequence[Sequence[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def ray_output(
    grid: Sequence[Sequence[int]],
    *,
    stop_at_any_nonzero: bool = False,
    use_rightmost_maroon: bool = False,
    nearest_maroon_direction: bool = False,
    emitter_limit: int | None = None,
) -> list[list[int]]:
    """Independent executable interpretation and controlled rival variants."""
    h, w = _shape(grid)
    out = [list(row) for row in grid]
    emitters = sorted(positions(grid, 4))
    if emitter_limit is not None:
        emitters = emitters[:emitter_limit]

    for row, source_col in emitters:
        direction = 1
        stop_col: int | None = None
        maroons = [col for col, value in enumerate(grid[row]) if value == 9]
        right_maroons = [col for col in maroons if col > source_col]
        if nearest_maroon_direction and maroons:
            stop_col = min(maroons, key=lambda col: (abs(col - source_col), col))
            direction = 1 if stop_col > source_col else -1
        elif use_rightmost_maroon and right_maroons:
            stop_col = max(right_maroons)
        elif right_maroons:
            stop_col = min(right_maroons)

        col = source_col + direction
        while 0 <= col < w:
            value = grid[row][col]
            if stop_col is not None and col == stop_col:
                break
            if stop_at_any_nonzero and value != 0:
                break
            if value == 9 and not (use_rightmost_maroon or nearest_maroon_direction):
                break
            if value == 0:
                out[row][col] = 8
            col += direction
    return out


def classify_scene(grid: Sequence[Sequence[int]]) -> str:
    _shape(grid)
    if any(value == 2 for row in grid for value in row):
        return "pass_through_distractor"
    for row in grid:
        emitters = [col for col, value in enumerate(row) if value == 4]
        if len(emitters) != 1:
            continue
        source = emitters[0]
        left = [col for col, value in enumerate(row) if value == 9 and col < source]
        right = [col for col, value in enumerate(row) if value == 9 and col > source]
        if left and len(right) >= 2:
            return "multi_blocker"
    return "canonical"


def observed(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    h, w = _shape(grid)
    return {
        "grid_h": h,
        "grid_w": w,
        "emitter_count": len(positions(grid, 4)),
        "scene_kind": classify_scene(grid),
    }


def pass_through_witness() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(6)]
    grid[1][1] = 4
    grid[1][3] = 2
    grid[1][6] = 9
    return grid


def multi_blocker_witness() -> list[list[int]]:
    grid = [[0] * 10 for _ in range(6)]
    grid[2][1] = 9
    grid[2][3] = 4
    grid[2][6] = 9
    grid[2][9] = 9
    return grid


def _survivors(gen, demos: Sequence[dict[str, Any]]) -> list[str]:
    return sorted(
        name
        for name, rival in gen.LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    )


def audit(gen=None, *, starts: int = 12, seeds: Iterable[int] = (1, 91), bands=("easy", "medium", "hard")) -> dict[str, Any]:
    gen = gen or load_generator()
    canonical = canonical_pairs()
    shortcut_rows = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        shortcut_rows[name] = {"matches": matches, "total": len(canonical)}

    band_rows = {}
    for band in bands:
        failures = []
        unique = set()
        profile_counts: dict[str, int] = {}
        for seed in seeds:
            for start in range(starts):
                demos = []
                for index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, index, difficulty=band)
                    unique.add(repr(grid))
                    profile = gen.schedule_profile(seed, index, band)
                    profile_counts[profile] = profile_counts.get(profile, 0) + 1
                    demos.append({"input": grid, "output": ray_output(grid)})
                survivors = _survivors(gen, demos)
                if survivors:
                    failures.append({"seed": seed, "start": start, "survivors": survivors})
        band_rows[band] = {
            "lesson_contract_failures": failures,
            "unique_inputs": len(unique),
            "profile_counts": profile_counts,
        }

    return {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(
            Path(gen.__file__).read_bytes()
        ).hexdigest(),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_shortcuts": shortcut_rows,
        "lesson_competitors": sorted(gen.LESSON_COMPETITORS),
        "by_band": band_rows,
        "passed": all(not row["lesson_contract_failures"] for row in band_rows.values()),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
