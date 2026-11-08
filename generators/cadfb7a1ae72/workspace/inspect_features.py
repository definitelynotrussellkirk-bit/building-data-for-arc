#!/usr/bin/env python3
"""Inspect object features and rival-rule disagreements for cadfb7a1ae72.

Examples, from the repository root:

    PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/inspect_features.py \
        --sample-index 3 --seed 1234 --difficulty medium

    PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/inspect_features.py \
        --canonical 0

    PYTHONPATH=shared/runtime python3 generators/cadfb7a1ae72/workspace/inspect_features.py \
        --grid some_grid.json --out report.json
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "cadfb7a1ae72"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"inspect_{TASK_ID}_generator", TASK_DIR / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load task generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
_SYMMETRY_NAMES = {
    0: "none",
    1: "row-only",
    2: "column-only",
    3: "row-and-column",
}


def _canonical_pairs() -> list[dict[str, Any]]:
    ledger = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    pairs: list[dict[str, Any]] = []
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            values = row.get(split) or []
            if isinstance(values, dict):
                values = [values]
            for pair in values:
                if not isinstance(pair, dict) or not pair.get("input"):
                    continue
                grid = pair["input"]
                if grid and isinstance(grid[0], str):
                    grid = [[int(char) for char in text] for text in grid]
                target = pair.get("output")
                if target and isinstance(target[0], str):
                    target = [[int(char) for char in text] for text in target]
                pairs.append({"split": split, "input": grid, "output": target})
    return pairs


def report_for_grid(grid: list[list[int]]) -> dict[str, Any]:
    """Return a JSON-ready feature table plus intended and rival matrices."""
    source = copy.deepcopy(grid)
    analysis = GEN._analyze(source)
    if analysis.get("errors"):
        return {
            "dimensions": [len(grid), len(grid[0]) if grid and grid[0] else 0],
            "analysis_errors": analysis["errors"],
        }

    intended = GEN.rule_mirror(source)
    rivals = {
        name: rival(source)
        for name, rival in GEN.SEMANTIC_RIVALS.items()
    }
    return {
        "task_id": TASK_ID,
        "dimensions": [analysis["grid_h"], analysis["grid_w"]],
        "palette": list(analysis["palette"]),
        "recognized_profile": analysis["profile"],
        "self_check": GEN.self_check(source),
        "strict_canonical_like": GEN.strict_canonical_like(source),
        "objects": [
            {
                "index": obj["index"],
                "color": obj["color"],
                "top_left": [obj["r1"], obj["c1"]],
                "bottom_right": [obj["r2"], obj["c2"]],
                "bbox": [obj["height"], obj["width"]],
                "area": obj["area"],
                "holes": obj["holes"],
                "enclosed_zero_cells": GEN._enclosed_zero_cell_count(
                    obj["normalized_cells"]
                ),
                "symmetry_class": obj["symmetry_class"],
                "symmetry_name": _SYMMETRY_NAMES[obj["symmetry_class"]],
                "projection_symmetry_class": GEN._projection_symmetry_class(
                    obj["normalized_cells"]
                ),
                "normalized_cells": [list(cell) for cell in obj["normalized_cells"]],
            }
            for obj in analysis["objects"]
        ],
        "intended_output": intended,
        "rivals": {
            name: {
                "output": output,
                "disagrees": output != intended,
                "first_disagreement": _first_disagreement(intended, output),
            }
            for name, output in rivals.items()
        },
    }


def _first_disagreement(
    intended: list[list[int]], rival: list[list[int]]
) -> dict[str, Any] | None:
    for row in range(len(intended)):
        for col in range(len(intended[row])):
            if intended[row][col] != rival[row][col]:
                return {
                    "index": [row, col],
                    "intended": intended[row][col],
                    "rival": rival[row][col],
                }
    return None


def _read_grid(path: Path) -> list[list[int]]:
    value = json.loads(path.read_text())
    if isinstance(value, dict) and "input" in value:
        value = value["input"]
    if not isinstance(value, list):
        raise ValueError("grid JSON must be a nested list or an object with an input field")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--grid", type=Path, help="JSON nested grid or {'input': grid}")
    source.add_argument(
        "--canonical",
        type=int,
        metavar="INDEX",
        help="inspect canonical pair by zero-based index (0..2)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    parser.add_argument("--profile", choices=GEN.PROFILES)
    parser.add_argument("--grid-h", type=int)
    parser.add_argument("--grid-w", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    canonical_target = None
    if args.grid is not None:
        grid = _read_grid(args.grid)
        origin = {"kind": "file", "path": str(args.grid)}
    elif args.canonical is not None:
        pairs = _canonical_pairs()
        if not 0 <= args.canonical < len(pairs):
            parser.error(f"--canonical must be 0..{len(pairs) - 1}")
        pair = pairs[args.canonical]
        grid = pair["input"]
        canonical_target = pair["output"]
        origin = {
            "kind": "canonical",
            "index": args.canonical,
            "split": pair["split"],
        }
    else:
        overrides = {
            key: value
            for key, value in {
                "profile": args.profile,
                "grid_h": args.grid_h,
                "grid_w": args.grid_w,
            }.items()
            if value is not None
        }
        grid = GEN.generate(
            args.seed,
            args.sample_index,
            difficulty=args.difficulty,
            **overrides,
        )
        origin = {
            "kind": "generated",
            "seed": args.seed,
            "sample_index": args.sample_index,
            "difficulty": args.difficulty,
            "overrides": overrides,
        }

    report = report_for_grid(grid)
    report["origin"] = origin
    report["input"] = grid
    if canonical_target is not None:
        report["canonical_output"] = canonical_target
        report["mirror_matches_canonical"] = report.get("intended_output") == canonical_target

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
