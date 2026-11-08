#!/usr/bin/env python3
"""Independent semantic probe for ARC task c3052979ff96.

This file deliberately reimplements the pixel rule instead of importing label
helpers from ``generator.py``.  It measures two review-critical alternatives:

* ``code_one_is_clockwise`` — the strongest canonical-fitting rival because the
  five canonical pairs contain codes 2, 3 and 4, but no code 1.
* ``strip_unrelated_objects`` — the historical distribution shortcut that
  deletes colors 5/6/7 before stamping the rotated source.

Run directly or through the packet wrapper::

    python3 generators/c3052979ff96/workspace/reference_probe.py \
      --generated 100 --json-out ../checks/reference-probe.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

TASK_ID = "c3052979ff96"
RULE_HASH = "a9dc0b2876d4"
HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = HOME.parents[1]
GENERATOR_PATH = HOME / "generator.py"

for _path in (REPO_ROOT / "shared/runtime", REPO_ROOT / "src", REPO_ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)

Grid = list[list[int]]
Point = tuple[int, int]


def normalize_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    rows: Grid = []
    width = None
    for row in grid:
        if isinstance(row, str):
            values = [int(value) for value in row]
        else:
            values = list(row)
        if width is None:
            width = len(values)
        if not values or len(values) != width:
            raise ValueError("grid must be nonempty and rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid cells must be integer ARC colors 0..9")
        rows.append(values)
    return rows


def canonical_pairs() -> list[dict[str, Grid]]:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    pairs: list[dict[str, Grid]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split) or []
                items = value if isinstance(value, list) else [value]
                for pair in items:
                    if isinstance(pair, dict) and "input" in pair and "output" in pair:
                        pairs.append(
                            {
                                "input": normalize_grid(pair["input"]),
                                "output": normalize_grid(pair["output"]),
                            }
                        )
    if not pairs:
        raise RuntimeError(f"canonical task {TASK_ID} has no labeled pairs")
    return pairs


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(path) if path is not None else GENERATOR_PATH
    spec = importlib.util.spec_from_file_location(
        f"reference_probe_generator_{TASK_ID}", selected
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _find_cells(grid: Grid, color: int) -> list[Point]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def control_code(grid: Grid) -> int:
    cells = [
        value
        for row in grid
        for value in row
        if 1 <= value <= 4
    ]
    if len(cells) != 1:
        raise ValueError(f"expected one control cell in 1..4, found {len(cells)}")
    return cells[0]


def rotate_point(pivot: Point, point: Point, code: int) -> Point:
    prow, pcol = pivot
    row, col = point
    drow, dcol = row - prow, col - pcol
    if code == 1:
        return prow + drow, pcol + dcol
    if code == 2:
        return prow + dcol, pcol - drow
    if code == 3:
        return prow - drow, pcol - dcol
    if code == 4:
        return prow - dcol, pcol + drow
    raise ValueError("code must be in 1..4")


def intended_output(grid: Any, *, code_override: int | None = None) -> Grid:
    source = normalize_grid(grid)
    pivot_cells = _find_cells(source, 9)
    shape_cells = _find_cells(source, 8)
    if len(pivot_cells) != 1 or not shape_cells:
        raise ValueError("expected one color-9 pivot and a color-8 source")
    code = control_code(source) if code_override is None else code_override
    output = copy.deepcopy(source)
    height, width = len(source), len(source[0])
    for point in shape_cells:
        row, col = rotate_point(pivot_cells[0], point, code)
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 2
    return output


def code_one_is_clockwise(grid: Any) -> Grid:
    source = normalize_grid(grid)
    code = control_code(source)
    return intended_output(source, code_override=2 if code == 1 else code)


def strip_unrelated_objects(grid: Any) -> Grid:
    stripped = normalize_grid(grid)
    for row, values in enumerate(stripped):
        for col, value in enumerate(values):
            if value in (5, 6, 7):
                stripped[row][col] = 0
    return intended_output(stripped)


def components(grid: Any, colors: tuple[int, ...] = (5, 6, 7)) -> list[set[Point]]:
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    allowed = set(colors)
    seen: set[Point] = set()
    result: list[set[Point]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or source[row][col] not in allowed:
                continue
            color = source[row][col]
            todo = [(row, col)]
            seen.add((row, col))
            component: set[Point] = set()
            while todo:
                r, c = todo.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and source[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(component)
    return result


def _diff_cells(left: Grid, right: Grid) -> list[list[int]]:
    return [
        [row, col, left[row][col], right[row][col]]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def analyze_grid(grid: Any) -> dict[str, Any]:
    source = normalize_grid(grid)
    intended = intended_output(source)
    code_rival = code_one_is_clockwise(source)
    strip_rival = strip_unrelated_objects(source)
    distractors = components(source)
    return {
        "height": len(source),
        "width": len(source[0]),
        "palette": sorted({value for row in source for value in row}),
        "code": control_code(source),
        "pivot": list(_find_cells(source, 9)[0]),
        "source_cells": [list(point) for point in _find_cells(source, 8)],
        "distractor_components": len(distractors),
        "distractor_cells": sum(map(len, distractors)),
        "intended_output": intended,
        "code_one_is_clockwise_output": code_rival,
        "strip_unrelated_objects_output": strip_rival,
        "code_one_is_clockwise_diff_cells": len(_diff_cells(intended, code_rival)),
        "strip_unrelated_objects_diff_cells": len(_diff_cells(intended, strip_rival)),
        "code_one_is_clockwise_differences": _diff_cells(intended, code_rival),
        "strip_unrelated_objects_differences": _diff_cells(intended, strip_rival),
    }


def canonical_report() -> dict[str, Any]:
    pairs = canonical_pairs()
    return {
        "pairs": len(pairs),
        "oracle_matches": sum(
            intended_output(pair["input"]) == pair["output"] for pair in pairs
        ),
        "code_one_is_clockwise_matches": sum(
            code_one_is_clockwise(pair["input"]) == pair["output"] for pair in pairs
        ),
        "strip_unrelated_objects_matches": sum(
            strip_unrelated_objects(pair["input"]) == pair["output"] for pair in pairs
        ),
        "canonical_codes": sorted({control_code(pair["input"]) for pair in pairs}),
    }


def build_report(generated: int, seed: int) -> dict[str, Any]:
    if generated < 0:
        raise ValueError("generated must be nonnegative")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    generator = load_generator()
    self_check_failures = []
    oracle_mismatches = []
    code_counterexamples = 0
    strip_counterexamples = 0
    codes: dict[str, int] = {}
    profiles: dict[str, int] = {}
    for index in range(generated):
        grid = generator.generate(seed, index)
        findings = generator.self_check(grid)
        if findings:
            self_check_failures.append({"index": index, "findings": findings})
        truth = intended_output(grid)
        if generator.rule_mirror(grid) != truth:
            oracle_mismatches.append(index)
        code = control_code(grid)
        codes[str(code)] = codes.get(str(code), 0) + 1
        profile = f"{len(grid)}x{len(grid[0])}p{len({v for row in grid for v in row})}"
        profiles[profile] = profiles.get(profile, 0) + 1
        code_counterexamples += int(code_one_is_clockwise(grid) != truth)
        strip_counterexamples += int(strip_unrelated_objects(grid) != truth)

    witness_grid = generator.generate(
        seed,
        0,
        grid_profile="13x13",
        code_value=1,
        shape_id=4,
        source_quadrant=2,
        n_distractors=4,
    )
    return {
        "schema": "c3052979ff96-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": RULE_HASH,
        "canonical": canonical_report(),
        "generated": {
            "draws": generated,
            "seed": seed,
            "self_check_failures": self_check_failures,
            "oracle_mismatches": oracle_mismatches,
            "code_counts": dict(sorted(codes.items())),
            "profile_counts": dict(sorted(profiles.items())),
            "code_one_counterexamples": code_counterexamples,
            "strip_counterexamples": strip_counterexamples,
        },
        "witness": {
            "generation": {
                "seed": seed,
                "sample_index": 0,
                "overrides": {
                    "grid_profile": "13x13",
                    "code_value": 1,
                    "shape_id": 4,
                    "source_quadrant": 2,
                    "n_distractors": 4,
                },
            },
            "input": witness_grid,
            "analysis": analyze_grid(witness_grid),
        },
        "scope_note": (
            "The Python oracle is an independent supplemental probe. "
            "The selected Racket rule remains the output authority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = build_report(args.generated, args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
