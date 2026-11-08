#!/usr/bin/env python3
"""Source-bound diagnostic probe for task 192d2bc2de61.

This complements, but does not replace, the Racket-backed battery and lesson
census.  It verifies the task module's declared shortcuts, witnesses, exact
profiles, and every query rotation of a bounded cyclic schedule.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "192d2bc2de61"
HOME = Path(__file__).resolve().parents[1]


def load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", HOME / "generator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legend(grid):
    return [value for value in grid[0] if value != 0]


def components(grid, color):
    remaining = {
        (r, c)
        for r in range(1, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    out = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        out.append(cells)
    return out


def crop(grid, cells):
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def pack(blocks):
    height = max(map(len, blocks))
    width = sum(len(block[0]) for block in blocks) + len(blocks) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for block in blocks:
        for r, row in enumerate(block):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(block[0]) + 1
    return out


def intended_output(grid):
    blocks = []
    for color in legend(grid):
        choices = sorted(
            components(grid, color),
            key=lambda cells: (-len(cells), min(r for r, _ in cells), min(c for _, c in cells)),
        )
        blocks.append(crop(grid, choices[0]))
    return pack(blocks)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(starts: int, unique_draws: int) -> dict[str, Any]:
    gen = load_generator()
    source_hash = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))

    shortcut_rows = {}
    for name, solver in sorted(gen.CANONICAL_SHORTCUTS.items()):
        matches = [solver(deepcopy(pair["input"])) == pair["output"] for pair in pairs]
        shortcut_rows[name] = {"matches": sum(matches), "total": len(matches), "all": all(matches)}

    profile_rows = []
    failures = []
    for band in (None, "easy", "medium", "hard"):
        for profile in gen.SCHEDULE_PROFILES:
            grid = gen.generate(271, 13, difficulty=band, scene_profile=profile)
            truth = intended_output(grid)
            row = {
                "band": band,
                "profile": profile,
                "shape": [len(grid), len(grid[0])],
                "palette_size": len({value for line in grid for value in line}),
                "self_check": gen.self_check(grid),
                "observed": gen.observe_overrides(grid),
                "witnesses": sorted(name for name, fn in gen.SEMANTIC_WITNESSES.items() if fn(grid)),
                "rivals_refuted": sorted(name for name, fn in gen.SEMANTIC_RIVALS.items() if fn(grid) != truth),
                "input_sha256": digest(grid),
            }
            profile_rows.append(row)
            if row["self_check"] or row["observed"] != {"scene_profile": profile}:
                failures.append(f"bad exact profile {band=} {profile=}")

    windows = []
    for band in (None, "easy", "medium", "hard"):
        for start in range(starts):
            sequence = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(811, start + offset, difficulty=band)
                sequence.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(len(sequence)):
                query = sequence[query_index]
                demos = [pair for index, pair in enumerate(sequence) if index != query_index]
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                survivors = []
                for name, solver in sorted(gen.LESSON_COMPETITORS.items()):
                    if all(solver(deepcopy(pair["input"])) == pair["output"] for pair in demos):
                        survivors.append(name)
                row = {
                    "band": band,
                    "start": start,
                    "query_index": query_index,
                    "profiles": [gen.observe_overrides(pair["input"])["scene_profile"] for pair in sequence],
                    "reasons": reasons,
                    "survivors": survivors,
                }
                windows.append(row)
                if reasons or survivors:
                    failures.append(
                        f"ambiguous window {band=} {start=} {query_index=}: reasons={reasons} survivors={survivors}"
                    )

    uniqueness = {}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(4000 + index, index, difficulty=band) for index in range(unique_draws)]
        uniqueness[band] = {
            "draws": unique_draws,
            "unique_inputs": len({digest(grid) for grid in grids}),
            "profiles": sorted({gen.observe_overrides(grid)["scene_profile"] for grid in grids}),
        }

    if not all(row["all"] for row in shortcut_rows.values()):
        failures.append("a declared canonical shortcut does not fit every canonical pair")

    return {
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "scope": "Python diagnostic mirror plus declared hooks; Racket authority is checked separately",
        "canonical_shortcuts": shortcut_rows,
        "profiles": profile_rows,
        "cyclic_rotations": {
            "starts_per_band": starts,
            "bands": 4,
            "rotations": len(windows),
            "failures": sum(bool(row["reasons"] or row["survivors"]) for row in windows),
            "rows": windows,
        },
        "uniqueness": uniqueness,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--unique-draws", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.starts < 1 or args.unique_draws < 1:
        parser.error("--starts and --unique-draws must be positive")
    result = run(args.starts, args.unique_draws)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": result["passed"],
        "generator_sha256": result["generator_sha256"],
        "rotations": result["cyclic_rotations"]["rotations"],
        "failures": len(result["failures"]),
        "out": str(args.out),
    }, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
